---
layout: post
title: "SCIM の resource versioning：ETag と条件付き request"
date: 2026-09-21 10:45:00 +0900
categories: [provisioning, scim, http]
---

<!--
Article brief
- Type: Feature Deep Dive
- Reader: SCIM 2.0 の resource versioning と競合検出を実装またはレビューする Service Provider / Client 開発者
- Question: SCIM の ETag と meta.version はどのように対応し、If-None-Match / If-Match をどこに配置して何を条件にするのか
- Answer: resource versioning は optional であること、ETag の HTTP header と meta.version の関係、weak ETag の扱い、If-None-Match による conditional retrieval と If-Match による PUT / PATCH の条件付き更新を区別できる
- Scope: RFC 7644 §3.14 と RFC 7643 §3.1 に定義された SCIM resource versioning、ETag、meta.version、If-None-Match、If-Match
- Out of scope: SCIM protocol version identifier、ETag の生成アルゴリズム、application-specific conflict resolution、Bulk operation、HTTP conditional request 一般の網羅的解説
- Primary sources: RFC 7644 §3.14; RFC 7643 §3.1; RFC 7232 §2.1, §2.3, §3.1, §3.2
- Diagram: ETag を取得した Client が conditional GET または If-Match 付き PUT / PATCH を送る flowchart
-->

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM 2.0 の resource versioning と競合検出を実装またはレビューする Service Provider / Client 開発者  
**この記事で伝えること:** SCIM の ETag と `meta.version` の関係、および `If-None-Match` / `If-Match` を使う条件付き request の仕様上の位置付け  
**扱わないこと:** SCIM protocol version identifier、ETag の生成アルゴリズム、application-specific conflict resolution、Bulk operation、HTTP conditional request 一般の網羅的解説

SCIM は resource の versioning に標準 HTTP ETag を利用します。ただし resource versioning のサポート自体は必須ではありません。RFC 7644 §3.14 は、Service Provider が weak ETag をサポートしてもよい（MAY）とし、conditional retrieval と Client 間の意図しない上書きの防止に ETag を利用できることを定めています。

この記事では、ETag がどこに現れ、Client がその値を subsequent request でどのように使用するかに範囲を限定します。

## 1. ETag と meta.version の関係

RFC 7644 §3.14 では、SCIM ETag をサポートする場合、ETag を HTTP response header として指定しなければなりません（MUST）。同じ値は resource の `meta.version` にも指定するべきです（SHOULD）。

RFC 7643 §3.1 は `meta.version` を Service Provider が割り当てる readOnly metadata として定義し、その値は resource representation の ETag HTTP response header と同じであるとしています。`meta.version` のサポートは optional で、Service Provider の versioning support に依存します。

以下は配置を確認するための**非規範的な例**です。ETag の opaque value は説明用です。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json
ETag: W/"illustrative-version-1"

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "id": "illustrative-user-id",
  "userName": "illustrative-user",
  "meta": {
    "version": "W/\"illustrative-version-1\""
  }
}
```

`ETag` は HTTP response header、`meta.version` は SCIM resource JSON object 内の member です。

## 2. weak ETag

RFC 7643 §3.1 は、Service Provider が `version` を提供し、その entity-tag の生成が RFC 7232 §2.1 の strong validator の特性をすべて満たさない場合、origin server が opaque value の前に `W/` を付けて weak として示さなければならない（MUST）と定めています。

したがって `W/"illustrative-version-1"` の `W/` は、SCIM 独自の JSON 記法ではなく HTTP entity-tag の weak indicator です。

## 3. If-None-Match による conditional retrieval

RFC 7644 §3.14 では、返された ETag を使い、Client が resource が変更された場合にだけ取得することを選んでもよい（MAY）としています。仕様例では `If-None-Match` request header を GET に配置しています。

以下は**非規範的な例**です。

```http
GET /Users/illustrative-user-id HTTP/1.1
Host: example.com
Accept: application/scim+json
If-None-Match: W/"illustrative-version-1"
```

resource が変更されていない場合、RFC 7644 §3.14 の例では Service Provider は empty body と HTTP `304 Not Modified` を返します。

```http
HTTP/1.1 304 Not Modified
```

`If-None-Match` は JSON request body の member ではなく HTTP request header です。

## 4. If-Match による条件付き PUT / PATCH

Service Provider が resource versioning をサポートする場合、RFC 7644 §3.14 は Client が PUT / PATCH operation に `If-Match` header を指定してもよい（MAY）としています。目的は、指定した ETag が Service Provider 上の最新 resource と一致する場合にだけ operation が成功するよう条件を付けることです。

以下は PATCH における配置を示す**非規範的な例**です。PATCH body は RFC 7644 §3.5.2 の構造に従い、値は説明用です。

```http
PATCH /Users/illustrative-user-id HTTP/1.1
Host: example.com
Content-Type: application/scim+json
If-Match: W/"illustrative-version-1"

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "replace",
      "path": "displayName",
      "value": "Illustrative Name"
    }
  ]
}
```

ここでも `If-Match` は HTTP request header であり、PatchOp JSON object の member ではありません。

## 5. request の流れ

<pre class="mermaid">
flowchart TD
    A[Resource response] --> B[ETag を取得]
    B --> C{次の操作}
    C --> D[GET + If-None-Match]
    C --> E[PUT / PATCH + If-Match]
    D --> F{Resource は変更済みか}
    F -->|No| G[304 Not Modified]
    F -->|Yes| H[Resource representation]
    E --> I{ETag は最新 resource と一致するか}
    I -->|Yes| J[Operation を実行]
    I -->|No| K[条件を満たさない]
</pre>

この図は RFC 7644 §3.14 が示す conditional retrieval と conditional modification の関係を簡略化したものです。ETag 不一致時の application-specific conflict resolution は追加していません。

## 6. versioning support は discovery できる

RFC 7643 §5 の ServiceProviderConfig には `etag` complex attribute があり、その `supported` sub-attribute は ETag operation をサポートするかを示す REQUIRED Boolean です。

以下は構造だけを示す**非規範的な最小例**です。

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
  "etag": {
    "supported": true
  }
}
```

ServiceProviderConfig 全体の capability discovery は別記事の範囲です。ここでは resource versioning を利用できるか確認する member としてのみ扱います。

## 7. 仕様上の境界

SCIM resource versioning について確認すべき点は次のとおりです。

- resource versioning のサポートは optional です（RFC 7644 §3.14）。
- ETag をサポートする場合、SCIM ETag は HTTP header に指定しなければなりません（MUST、RFC 7644 §3.14）。
- ETag は `meta.version` にも指定するべきです（SHOULD、RFC 7644 §3.14）。
- strong validator の特性を満たさない entity-tag は `W/` を付けて weak として示さなければなりません（MUST、RFC 7643 §3.1）。
- Client は conditional GET に `If-None-Match` を利用できます（MAY、RFC 7644 §3.14）。
- versioning をサポートする Service Provider に対し、Client は PUT / PATCH に `If-Match` を指定できます（MAY、RFC 7644 §3.14）。

ETag の生成方法や、条件を満たさなかった後にどのように変更内容を統合するかは、RFC 7644 §3.14 が特定の SCIM algorithm として定義している事項ではありません。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.14
- [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html) §3.1, §5
- [RFC 7232 — Hypertext Transfer Protocol (HTTP/1.1): Conditional Requests](https://www.rfc-editor.org/rfc/rfc7232.html) §2.1, §2.3, §3.1, §3.2
