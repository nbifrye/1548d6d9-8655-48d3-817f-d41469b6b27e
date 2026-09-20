---
layout: post
title: "RFC 9865：SCIM cursor-based pagination で次のページをどう取得するのか"
date: 2026-09-21 03:38:00 +0900
categories: [provisioning, scim]
tags: [SCIM, RFC9865, Pagination]
---

RFC 9865 は RFC 7643 と RFC 7644 を更新し、SCIM に cursor-based pagination を追加します。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM の検索結果を cursor でページングする Client / Service Provider を実装・レビューする開発者  
**この記事で伝えること:** `cursor` と `count` を使う request、`nextCursor` / `previousCursor` を返す response、後続ページ取得時に維持する query parameter の規則  
**扱わないこと:** RFC 7644 の `startIndex` による index-based pagination の詳細、sorting の詳細、cursor の内部生成方式、一般的な SCIM filter grammar

## Article brief

- **Reader:** SCIM cursor pagination を実装・レビューする Client / Service Provider 開発者。
- **Question:** 最初のページと後続ページで `cursor` をどこに置き、response のどの値を次の request に使うのか。
- **Answer:** GET / POST `/.search` での parameter 配置、`nextCursor` / `previousCursor` の意味、後続 request で維持する値、両 pagination method を提供する Service Provider の規則を追える。
- **Scope:** RFC 9865 §2–§4 の cursor-based pagination protocol。
- **Out of scope:** index-based pagination の詳細、sorting algorithm、cursor implementation、SCIM authorization model 全般。
- **Primary sources:** RFC 9865 §1–§4、参照上必要な RFC 7644 §3.4.3 / §4。
- **Diagram:** first request → ListResponse → `nextCursor` → next request の flowchart。

## 1. `cursor` はページ位置を表す opaque value である

RFC 9865 §2 は cursor-based pagination 用に `cursor` と `count` を定義します。

- `cursor`: URL-safe string。Client に対して opaque です。最初の cursor-paginated request では空文字列にするか、省略しなければなりません（MUST）。
- `count`: 1ページで要求する最大結果数です。指定した場合、Service Provider はその数を超えて返してはなりません（MUST NOT）が、少ない件数を返すことはできます（MAY）。負数は `0` と解釈します（SHALL）。`0` は resource result を返さず、`totalResults` だけを返す指定です。

GET の場合、これらは URL query parameter です。

以下は配置を示すための**非規範的な例**です。値は illustrative value です。

```http
GET /Users?cursor=&count=10 HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

## 2. response は次ページの `nextCursor` を返す

RFC 9865 §2 は `ListResponse` に `nextCursor` と `previousCursor` を追加します。

- `nextCursor`: 次ページ取得に使用できる cursor value。cursor pagination をサポートする Service Provider は、最終ページを除く paged response に含めなければなりません（MUST）。これを省略できるのは、後続ページがないことを示す場合だけです（MUST）。
- `previousCursor`: 前ページ取得に使用できる cursor value。返すこと自体が OPTIONAL です。最初のページでは返してはなりません（MUST NOT）。

以下は最小構造を示すための**非規範的な例**です。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:ListResponse"
  ],
  "totalResults": 42,
  "itemsPerPage": 10,
  "nextCursor": "illustrative-next-cursor",
  "Resources": []
}
```

`nextCursor` の値自体を Client が解釈することは RFC 9865 の protocol model ではありません。

## 3. 後続ページでは query を維持して cursor だけを進める

RFC 9865 §2 により、別ページを取得する Client は、最初の query と同じ Service Provider endpoint に対し、`cursor` を除くすべての query parameter と value を同一にして request しなければなりません（MUST）。`cursor` には、以前の response で返された `nextCursor` または `previousCursor` を設定するべきです（SHOULD）。

<pre class="mermaid">
flowchart TD
    A[最初の検索 request] --> B[ListResponse]
    B --> C[nextCursor を取得]
    C --> D[同じ query parameters を維持]
    D --> E[cursor を nextCursor に設定]
    E --> F[次ページを request]
</pre>

次は2ページ目を要求する**非規範的な例**です。

```http
GET /Users?cursor=illustrative-next-cursor&count=10 HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

## 4. POST `/.search` では JSON member に置く

RFC 9865 §3 は RFC 7644 §3.4.3 の POST `/.search` に cursor pagination を適用します。この場合 `cursor` と `count` は query string ではなく SearchRequest の JSON member です。

以下は配置を示すための**非規範的な例**です。

```http
POST /Users/.search HTTP/1.1
Host: scim.example
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:SearchRequest"
  ],
  "cursor": "",
  "count": 10
}
```

response は GET と同様に `ListResponse` で `nextCursor` を返せます。

## 5. cursor error が追加される

RFC 9865 §2.1 は HTTP 400 の SCIM error response で使用する pagination error type を追加します。

- `invalidCursor`: cursor value が invalid。
- `expiredCursor`: cursor が期限切れ。
- `invalidCount`: count value が invalid。

RFC 9865 §2.1 は invalid pagination parameter その他の error condition について、RFC 7644 §3.12 の HTTP status code と JSON error response を返すべきであるとしています（SHOULD）。

## 6. cursor と index の両方を実装する場合

RFC 9865 §2.4 は、Service Provider が cursor-based と index-based の両 pagination method をサポートする場合、Client が `cursor` または `startIndex` によって方式を指定できると規定します。

両方式をサポートする Service Provider は、pagination parameter が指定されなかった request に使用する default pagination method を選ばなければなりません（MUST）。

この section は両方式の共存時の protocol rule のみを扱います。`startIndex` / `count` による index-based pagination 自体の処理は別記事の範囲です。

## 7. Service Provider Configuration で capability を表せる

RFC 9865 §4 は `/ServiceProviderConfig` に `pagination` complex attribute を追加します。cursor pagination を実装する Service Provider は、この attribute を含めるべきです（SHOULD）。`pagination` attribute 自体は OPTIONAL です。

その sub-attribute として、`cursor` と `index` は Boolean で REQUIRED、`defaultPaginationMethod`、`defaultPageSize`、`maxPageSize`、`cursorTimeout` は OPTIONAL です。

以下は構造を示すための**非規範的な最小例**です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"
  ],
  "pagination": {
    "cursor": true,
    "index": true,
    "defaultPaginationMethod": "cursor"
  }
}
```

RFC 9865 §4 は、これら optional configuration value が公開されていないことを、default や page-size limit、cursor lifetime が存在しないという意味に Client が解釈してはならないと規定しています（MUST NOT）。

## 8. index-based pagination とのテーマ境界

RFC 7644 §3.4.2.4 の index-based pagination は `startIndex` で結果集合内の位置を指定します。一方、RFC 9865 の cursor-based pagination は Service Provider が返した opaque cursor を後続 request に渡します。

この記事では RFC 9865 の cursor protocol だけを扱い、両方式の優劣は評価しません。RFC 9865 自身も、2つの pagination pattern の利点・欠点を比較することを目的としていません。

## 一次資料

- RFC Editor: [RFC 9865 — Cursor-Based Pagination of System of Cross-domain Identity Management (SCIM) Resources](https://www.rfc-editor.org/rfc/rfc9865.html)
- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)

参照した主要節: RFC 9865 §1, §2, §2.1, §2.3, §2.4, §3, §4; RFC 7644 §3.4.3, §4  
最終確認: 2026-09-21
