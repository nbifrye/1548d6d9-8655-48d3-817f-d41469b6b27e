---
layout: post
title: "SCIM の認証と認可：仕様が定義すること・定義しないこと"
date: 2026-09-21 09:43:00 +0900
categories: [provisioning, scim, security]
---

<!--
Article brief
- Type: Requirement
- Reader: SCIM 2.0 Service Provider / Client の認証・認可境界を実装またはレビューする開発者
- Question: SCIM は認証方式や認可モデルをどこまで定義し、Service Provider に何を要求しているのか
- Answer: SCIM 固有の認証・認可方式は定義されず、標準 HTTP/TLS の仕組みを利用すること、認証済み Client を access control policy に対応付けること、Bearer Token・anonymous request・TLS に関する規範要件を区別できる
- Scope: RFC 7644 §2, §2.1, §2.2, §7.2, §7.4 に定義された authentication / authorization の境界と規範要件
- Out of scope: OAuth token endpoint / grant flow、scope の設計、個別 deployment の access control policy、SCIM resource CRUD の詳細、認証方式の優劣評価
- Primary sources: RFC 7644; RFC 6750
- Diagram: request の認証情報から authenticated client / subject を識別し、local access control policy により resource operation の認可を判断する flowchart
-->

## この記事について

**記事タイプ:** Requirement  
**対象読者:** SCIM 2.0 Service Provider / Client の認証・認可境界を実装またはレビューする開発者  
**この記事で伝えること:** SCIM が認証・認可について定義する範囲と、Service Provider / Client に課す規範要件  
**扱わないこと:** OAuth token endpoint / grant flow、scope の設計、個別 deployment の access control policy、SCIM resource CRUD の詳細、認証方式の優劣評価

SCIM は HTTP ベースの protocol ですが、SCIM 固有の authentication / authorization scheme は定義していません。RFC 7644 §2 は TLS および標準 HTTP authentication / authorization scheme を利用する構成を示し、具体的な authorization model と authenticated client を security subject に対応付ける方法は仕様の scope 外としています。

一方で、方式の選択を deployment に委ねることと、SCIM に security requirement がないことは同じではありません。RFC 7644 は authenticated client と access control policy の対応付け、HTTP authentication scheme の提示、TLS、Bearer Token を使用する場合の処理について規範要件を定めています。

## 1. SCIM 固有の認証・認可方式は定義されない

RFC 7644 §2 は、SCIM protocol 自体では SCIM-specific authentication / authorization scheme を定義しないとしています。例として TLS client authentication、HOBA、Bearer Token、Basic Authentication が説明されていますが、特定方式を SCIM 共通の必須方式として指定しているわけではありません。

Bearer Token は TLS と OAuth 2.0 などの token framework を組み合わせる場合に使用してもよい（MAY）とされています（RFC 7644 §2）。仕様中の protocol example が Bearer Token を使うことについても、Bearer Token を preferred method とする意味ではないと明記されています。

したがって、SCIM の interoperability requirement と、deployment が採用する具体的 authentication mechanism は区別する必要があります。

## 2. Service Provider は authenticated client を access control policy に対応付ける

RFC 7644 §2 は、authentication methodology にかかわらず、Service Provider が authenticated client を access control policy に対応付け、SCIM resource の取得・更新を認可するか判断できなければならない（MUST）と定めています。

また Service Provider は request を処理するとき、request を実行する subject と、対象 resource に対してその action が適切かを考慮するべき（SHOULD）としています。subject は通常、request の `Authorization` header から直接または間接に決定されます。

ただし、authorization model と、その mapping を実現する process 自体は RFC 7644 の scope 外です。仕様は role model、permission set、scope taxonomy など特定の access control design を要求していません。

<pre class="mermaid">
flowchart TD
    A[SCIM request] --> B[認証情報を処理]
    B --> C[Client / subject を識別]
    C --> D[local access control policy に対応付け]
    D --> E[対象 resource / action の認可を判断]
</pre>

この図は RFC 7644 §2 の関係を簡略化したもので、特定の authentication scheme や policy model を追加していません。

## 3. HTTP authentication scheme の提示

RFC 7644 §2 は、Service Provider がサポートする HTTP authentication scheme を `WWW-Authenticate` header で示すことを SHALL としています。

`WWW-Authenticate` は HTTP response header です。どの scheme を採用するかは SCIM が一律に決めていないため、header value は deployment がサポートする HTTP authentication scheme に依存します。

## 4. Bearer Token を使う場合の Authorization header

RFC 7644 §2 の protocol example は OAuth 2.0 Bearer Token を `Authorization` request header に配置しています。RFC 6750 §2.1 は Authorization Request Header Field による Bearer Token の送信形式を定義しています。

以下は配置を確認するための**非規範的な例**です。`illustrative-token-value` は説明用の値です。

```http
GET /Users/illustrative-user-id HTTP/1.1
Host: example.com
Accept: application/scim+json
Authorization: Bearer illustrative-token-value
```

この例は Bearer Token を他の authentication mechanism より推奨するものではありません。

RFC 7644 §2 は、Bearer Token を利用する Service Provider が、関連する authentication / authorization information を得るために token を validate、parse、または introspect する方法を持つことを前提としています。その具体的方法は token-issuing system により定義され、SCIM の scope 外です。

## 5. authorization grant を表す token

RFC 7644 §2.1 は、OAuth などが発行する authorization grant を表す Bearer Token または PoP Token を使う場合、local access control rule を評価するときに、authorization の種類、authorized scope、authorization から対応付ける security subject を考慮するべき（SHOULD）としています。

OAuth authorization token を使用する実装は、RFC 7521 §8 に記載された client authorization の threat と countermeasure を考慮しなければなりません（MUST、RFC 7644 §2.1）。他の token format / framework を使用する場合も、関連仕様が定める同種の threat と countermeasure を考慮しなければなりません（MUST）。

どの scope や subject mapping を採用するかはこの記事の scope 外です。

## 6. anonymous request は deployment によって許可され得る

RFC 7644 §2.2 は、一部の deployment では unauthenticated request を許可してもよい（MAY）としています。例として、Service Provider が anonymous client から User self-registration の Create request を受け入れる場合が示されています。

これは anonymous access を一般に要求する規定ではありません。許可するかどうかは deployment の判断であり、RFC 7644 §7.6 に anonymous request の security consideration が定められています。

## 7. SCIM 通信と TLS

RFC 7644 §7.2 は、SCIM resource が password を含む sensitive information を持ち得るため、SCIM Client と Service Provider が通信時に transport-layer security mechanism の使用を要求しなければならない（MUST）としています。

同 section は Service Provider が TLS 1.2 をサポートしなければならない（MUST）、Client が TLS 使用時に server identity check を行わなければならない（MUST）とも定めています。追加の transport-layer mechanism は Service Provider の security requirement を満たす場合にサポートしてもよい（MAY）とされています。

RFC 7644 §7.4 は Bearer Token と HTTP cookie を TLS で交換しなければならない（MUST）とし、Bearer Token については Service Provider が直接または間接に判定できる limited lifetime を持たなければならない（MUST）としています。

## 8. SCIM が決める境界

RFC 7644 が定める中心点は、特定の authentication product や authorization policy ではなく、SCIM request を access control decision へ接続するための protocol-level requirement です。

- SCIM-specific authentication / authorization scheme は定義しない（RFC 7644 §2）。
- Service Provider は authenticated client を access control policy に対応付けられなければならない（MUST、§2）。
- supported HTTP authentication scheme は `WWW-Authenticate` で示す（SHALL、§2）。
- anonymous request は deployment により許可してもよい（MAY、§2.2）。
- SCIM 通信には transport-layer security mechanism を要求する（MUST、§7.2）。
- Bearer Token を使う場合には §2.1 / §7.4 の token-specific requirement が適用される。

具体的な authorization model と mapping process は仕様の scope 外であるため、RFC 7644 だけから特定方式を必須または推奨とすることはできません。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §2, §2.1, §2.2, §7.2, §7.4
- [RFC 6750 — The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750.html) §2.1
