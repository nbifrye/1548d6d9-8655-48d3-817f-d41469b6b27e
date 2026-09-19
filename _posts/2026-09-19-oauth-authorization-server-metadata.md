---
layout: post
title: "RFC 8414：Authorization Server Metadata はどこから取得し、何を検証するのか"
date: 2026-09-19 09:41:00 +0900
categories: [oauth, discovery]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 Client で Authorization Server の endpoint と capability を取得する処理を実装・レビューする開発者  
**この記事で伝えること:** RFC 8414 に基づき、issuer identifier から metadata URL を構成し、HTTP GET で JSON object を取得して `issuer` を検証するまでの流れ  
**扱わないこと:** OpenID Connect Discovery 固有の処理、Authorization Server の選択方法、Dynamic Client Registration、個々の OAuth grant の実行、signed metadata の詳細

## Article brief

- **Reader:** Authorization Server Metadata の取得・検証を実装する OAuth 2.0 Client 開発者
- **Question:** issuer identifier から metadata をどの URL で取得し、取得した JSON の何を検証するのか
- **Answer:** RFC 8414 §2、§3、§3.1–§3.3 に基づき、well-known URL の構成、GET request、JSON response、`issuer` 一致検証を説明できる
- **Scope:** RFC 8414 §1、§2、§3、§3.1、§3.2、§3.3
- **Out of scope:** OpenID Connect Discovery の discovery procedure、signed metadata の処理詳細、Authorization Server の選択、各 endpoint の protocol processing
- **Primary sources:** RFC 8414
- **Diagram:** issuer identifier から metadata URL を構成し、取得した JSON の `issuer` を照合する処理を縦方向の flowchart で示す

## 1. Metadata は Authorization Server の構成を表す JSON object である

RFC 8414 §1 は、Authorization Server Metadata を、Client が Authorization Server と対話するために必要な endpoint location や capability を取得できる metadata format として定義しています。metadata は well-known location から JSON document として取得します。

RFC 8414 §2 では metadata member を定義しています。代表的なものは次のとおりです。

- **`issuer`:** REQUIRED。Authorization Server の issuer identifier。`https` scheme の URL で、query component と fragment component を含みません。
- **`authorization_endpoint`:** Authorization Endpoint の URL。Authorization Endpoint を使う grant type を1つもサポートしない場合を除き REQUIRED。
- **`token_endpoint`:** Token Endpoint の URL。implicit grant type だけをサポートする場合を除き REQUIRED。
- **`jwks_uri`:** OPTIONAL。Authorization Server の JWK Set document の URL。この URL は `https` scheme を使わなければなりません（MUST, §2）。
- **`scopes_supported`:** RECOMMENDED。サポートする OAuth 2.0 scope value の JSON array。
- **`response_types_supported`:** REQUIRED。サポートする `response_type` value の JSON array。
- **`grant_types_supported`:** OPTIONAL。サポートする grant type value の JSON array。
- **`introspection_endpoint`:** OPTIONAL。RFC 7662 の Introspection Endpoint URL。

この記事では、これらすべての metadata member を列挙するのではなく、取得と検証の流れを理解するために必要な member に限定します。

## 2. issuer identifier から well-known URL を構成する

RFC 8414 §3 は、Authorization Server Metadata を well-known location に公開する方法を定義しています。default の well-known URI string は `/.well-known/oauth-authorization-server` です。

issuer identifier に path component がない場合、たとえば issuer が次の場合を考えます。

```text
https://authorization.example
```

metadata URL は次の形になります。

```text
https://authorization.example/.well-known/oauth-authorization-server
```

issuer identifier に path component がある場合、RFC 8414 §3.1 は well-known URI string を host component と path component の間に挿入します。issuer が次の場合、

```text
https://authorization.example/issuer1
```

取得先は次の形です。

```text
https://authorization.example/.well-known/oauth-authorization-server/issuer1
```

issuer identifier の path component 末尾に `/` がある場合は、挿入前にその `/` を除かなければなりません（MUST, §3.1）。

## 3. Client は metadata を HTTP GET で取得する

RFC 8414 §3.1 は、Client が metadata document を HTTP `GET` request で問い合わせなければならない（MUST）と規定しています。

次は RFC 8414 §3.1 の構造に沿った非規範的な例です。

```http
GET /.well-known/oauth-authorization-server HTTP/1.1
Host: authorization.example
```

この request に JSON request body はありません。metadata は URL の well-known path を HTTP GET して取得します。

<pre class="mermaid">
flowchart TD
    A[issuer identifier] --> B[well-known URL を構成]
    B --> C[HTTP GET]
    C --> D[metadata JSON]
    D --> E{issuer は一致するか}
    E -->|一致| F[metadata を使用]
    E -->|不一致| G[metadata を使用しない]
</pre>

## 4. Response は `application/json` の JSON object である

RFC 8414 §3.2 は、成功 response が HTTP `200 OK` を使用し（MUST）、`application/json` content type の JSON object を返すこと（MUST）を規定しています。複数の値を返す claim は JSON array で表します。要素数が0の claim は response から省略しなければなりません（MUST）。

次は RFC 8414 §2 と §3.2 で定義された member だけを使った、構造を確認するための非規範的な例です。

```json
{
  "issuer": "https://authorization.example",
  "authorization_endpoint": "https://authorization.example/authorize",
  "token_endpoint": "https://authorization.example/token",
  "jwks_uri": "https://authorization.example/jwks.json",
  "scopes_supported": ["read", "profile"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code"],
  "introspection_endpoint": "https://authorization.example/introspect"
}
```

この object では、endpoint location は top-level string、複数の capability は top-level JSON array として配置されます。たとえば `response_types_supported` は REQUIRED、`grant_types_supported` は OPTIONAL です（§2）。

## 5. Client は取得元の issuer と response の `issuer` を一致させる

RFC 8414 §3.3 は、metadata response の `issuer` value が、metadata URL を作る際に使用した Authorization Server の issuer identifier と同一でなければならない（MUST）と規定しています。

値が同一でない場合、Client は response に含まれる data を使用してはなりません（MUST NOT, §3.3）。

たとえば Client が次の issuer identifier から metadata URL を構成した場合、

```text
https://authorization.example
```

response の `issuer` は次と同一である必要があります。

```json
{
  "issuer": "https://authorization.example"
}
```

この検証は endpoint URL の存在確認とは別の処理です。RFC 8414 §3.3 がここで要求しているのは、metadata URL の基礎にした issuer identifier と、取得した metadata の `issuer` value の同一性確認です。

## 6. TLS に関する要件

RFC 8414 §6.1 は implementation が TLS をサポートしなければならない（MUST）と規定しています。また、この RFC が規定する Authorization Server は TLS 1.2 をサポートしなければならず（MUST）、Client は TLS を使用するとき server certificate check を実施しなければなりません（MUST）。

この記事では TLS version の選択や certificate validation algorithm の詳細には踏み込みません。

## 一次資料

- RFC Editor: [RFC 8414 — OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414.html)

参照した主要節: §1, §2, §3, §3.1, §3.2, §3.3, §6.1  
最終確認: 2026-09-19
