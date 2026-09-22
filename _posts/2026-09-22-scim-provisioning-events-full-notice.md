---
layout: post
title: "SCIM Provisioning Events：full と notice の payload 構造"
date: 2026-09-22 09:41:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Feature Deep Dive
- Reader: SCIM の resource change を Security Event Token で受信・発行する Event Publisher / Event Receiver の実装者
- Question: RFC 9967 の provisioning event で `full` と `notice` は何を表し、`data` / `attributes` はどこに配置されるのか
- Answer: provisioning event URI の `full` / `notice` と payload member の対応、`sub_id` による subject identification、notice 受信後に仕様上可能な SCIM GET の関係を説明できる
- Scope: RFC 9967 §2, §2.1, §2.2, §2.4 の provisioning event の共通構造と full / notice の差異
- Out of scope: feed:add / feed:remove、個別 create / patch / put / delete / activate / deactivate event の詳細、SET delivery protocol、asynchronous SCIM request、ServiceProviderConfig の event discovery、署名・暗号化・security considerations
- Primary sources: RFC 9967 §2, §2.1, §2.2, §2.4; RFC 8417 §2
- Diagram: SCIM resource state change から Event Publisher が full または notice の SET を Event Receiver に渡す関係を示す flowchart TD
-->

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM の resource change を Security Event Token で受信・発行する Event Publisher / Event Receiver の実装者  
**この記事で伝えること:** provisioning event URI の `full` / `notice` と `data` / `attributes` payload の対応  
**扱わないこと:** feed event、個別 provisioning event の詳細、SET delivery protocol、asynchronous SCIM request、event discovery、署名・暗号化

RFC 9967 は、SCIM service provider で発生した resource state change を Security Event Token（SET）で表す SCIM Security Events を定義しています。この記事では、そのうち RFC 9967 §2.4 の provisioning event における `full` と `notice` の payload 構造だけを扱います。

**A `full` event carries `data`; a `notice` event carries `attributes`, and exactly one of them is present.**  
（`full` event は `data` を運び、`notice` event は `attributes` を運びます。両者のうち存在するのは正確に一方だけです。）

## 1. SCIM Event は SET の `events` claim に入る

RFC 9967 §2 によると、SCIM Event は RFC 8417 の Security Event Token として表現されます。SET には standard JWT top-level claim と `events` claim があり、`events` object では event URI が member name、その値が event information を含む JSON object になります。

RFC 9967 は SCIM Event 用に `urn:ietf:params:scim:event` prefix を定義しています。provisioning event の prefix は §2.4 の `urn:ietf:params:scim:event:prov` です。

## 2. subject は top-level の `sub_id` で識別する

RFC 9967 §2.1 では、SCIM Event は event subject の識別に RFC 9493 の `sub_id` claim を使用しなければなりません（MUST）。`sub_id` は main JWT claims body に置かなければならず（MUST）、`events` claim 内の event payload に置いてはなりません（MUST NOT）。JWT の `sub` claim を subject identification に使用してはなりません（MUST NOT）。

`sub_id` object では `format` を `scim` とし、SCIM resource の relative path を示す `uri` を含めます。RFC 9967 §2.1 は、この `uri` を SCIM Event の `sub_id` claim に含めることを MUST としています。

以下は配置だけを示す**非規範的な最小構造例**です。値は illustrative value です。

```json
{
  "iss": "https://issuer.example",
  "iat": 1770000000,
  "aud": "https://receiver.example",
  "sub_id": {
    "format": "scim",
    "uri": "/Users/illustrative-user-id"
  },
  "events": {
    "urn:ietf:params:scim:event:prov:patch:notice": {
      "attributes": ["displayName"]
    }
  }
}
```

この例では `sub_id` は top-level claim、`attributes` は `events` 内の event payload member です。JWT/SET の serialization や署名方法はこの記事の scope 外です。

## 3. `full` と `notice` は event URI と payload が対応する

RFC 9967 §2.4 は provisioning event について、`data` payload attribute を含む場合、event URI が `full` で終わらなければならない（MUST）と規定しています。それ以外の場合、event URI は `notice` で終わります。

さらに §2.4 は `data` と `attributes` のうち正確に一方だけが存在しなければならず（MUST）、両方を同時に含めてはならない（MUST NOT）と定めています。

- `full`: event payload に `data` を含みます。`data` は service provider における resource の final representation を反映する値を運びます。
- `notice`: event payload に `attributes` を含みます。`attributes` は request で作成または変更された attribute の集合を列挙します。

RFC 9967 §2.2 では、`attributes` は array であり、変更された attribute 名は RFC 7644 §3.5.2 の `path` ABNF に従うことが SHOULD とされています。

## 4. 非規範的な `full` event payload 例

以下は `full` の配置と最小構造を示す**非規範的な例**です。illustrative identifier と attribute value に追加の規範的意味はありません。

```json
{
  "sub_id": {
    "format": "scim",
    "uri": "/Users/illustrative-user-id"
  },
  "events": {
    "urn:ietf:params:scim:event:prov:create:full": {
      "data": {
        "schemas": [
          "urn:ietf:params:scim:schemas:core:2.0:User"
        ],
        "userName": "illustrative-user"
      }
    }
  }
}
```

`data` は `events` object の event URI member の値である JSON object の中に配置されます。RFC 9967 §2.2 は `data` を、RFC 7644 §3.7 の SCIM Bulk Operations の `data` attribute で説明される情報を含む event payload attribute と定義しています。

## 5. 非規範的な `notice` event payload 例

以下は同じ配置関係を `notice` で示す**非規範的な例**です。

```json
{
  "sub_id": {
    "format": "scim",
    "uri": "/Users/illustrative-user-id"
  },
  "events": {
    "urn:ietf:params:scim:event:prov:create:notice": {
      "attributes": [
        "userName"
      ]
    }
  }
}
```

`notice` は変更された attribute 名を通知しますが、その attribute の実際の値を伝える形式ではありません。RFC 9967 §2.4.1 は create notice の Event Receiver が、提供された `sub_id` に基づいて SCIM GET を実行し、その情報を取得してもよい（MAY）としています。

## 6. full / notice と Event Receiver の関係

<pre class="mermaid">
flowchart TD
    A[SCIM resource state change]
    B[Event Publisher issues SET]
    C{Provisioning event mode}
    D[full: data payload]
    E[notice: attributes payload]
    F[Event Receiver]
    A --> B
    B --> C
    C --> D
    C --> E
    D --> F
    E --> F
</pre>

この図は RFC 9967 §2.4 の payload variation だけを示します。SET の push / poll delivery、receiver の local processing、security property は追加していません。

## 7. `full` / `notice` が適用される provisioning event

RFC 9967 §2.4 は resource change の provisioning event として create、patch、put、delete、activate、deactivate を定義しています。このうち create / patch / put では event URI に `{notice|full}` variation が定義されています。各 operation 固有の payload semantics はそれぞれ §2.4.1–§2.4.6 の論点であり、この記事では共通する `full` / `notice` の構造に限定します。

この記事で確認する対応関係は次のとおりです。

1. SCIM Event は SET の `events` claim 内で event URI と JSON event payload により表現されます（RFC 9967 §2）。
2. subject は top-level `sub_id` で識別します（MUST、§2.1）。
3. `data` を含む provisioning event URI は `full` で終わらなければなりません（MUST、§2.4）。
4. `notice` では `attributes` が変更 attribute の集合を表します（§2.4）。
5. `data` と `attributes` は正確に一方だけを含めなければならず（MUST）、同時に含めてはなりません（MUST NOT、§2.4）。

## 一次資料

- [RFC 9967 — System for Cross-Domain Identity Management (SCIM) Profile for Security Event Tokens (SETs)](https://www.rfc-editor.org/rfc/rfc9967.html) §2, §2.1, §2.2, §2.4
- [RFC 8417 — Security Event Token (SET)](https://www.rfc-editor.org/rfc/rfc8417.html) §2
