---
layout: post
title: "RFC 7662：Token Introspection の active は何を表すのか"
date: 2026-09-19 08:39:00 +0900
categories: [oauth, token]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** OAuth 2.0 の Protected Resource / Authorization Server で Token Introspection を実装・レビューする開発者  
**この記事で伝えること:** RFC 7662 の Introspection Request / Response と、`active` が表す状態および Authorization Server が行う適用可能な検査  
**扱わないこと:** JWT Access Token のローカル検証、Token Revocation Endpoint、Client が Access Token を取得するフロー、個別 deployment の認可ポリシー

## 1. Introspection Endpoint が返すもの

RFC 7662 §2 は Introspection Endpoint を、OAuth 2.0 token を表す parameter を受け取り、その token の meta-information を JSON document として返す endpoint と定義しています。この情報には token が現在 active かどうかが含まれます。

RFC 7662 における active token の具体的な定義は Authorization Server に依存します。§2 は一般的な例として、その Authorization Server が発行し、expired でも revoked でもなく、introspection を行う Protected Resource で使用可能な token を挙げています。

この定義は、すべての deployment に同一の追加条件を要求するものではありません。§4 は、どの check が適用されるかを Authorization Server が判断するとしています。

## 2. Protected Resource は token を POST する

RFC 7662 §2.1 では、Protected Resource は Introspection Endpoint に HTTP POST request を送り、parameter を `application/x-www-form-urlencoded` 形式で送信します。

`token` parameter は REQUIRED です。値には introspection の対象となる token string を指定します。

`token_type_hint` は OPTIONAL です。Protected Resource は token lookup の最適化を助けるためにこの parameter を送ることができます（MAY）。Authorization Server が hint で token を見つけられない場合、サポートするすべての token type に検索を広げなければなりません（MUST）。Authorization Server はこの parameter を無視することもできます（MAY）。

また、Introspection Endpoint は token scanning attack を防ぐため、endpoint へのアクセスに何らかの authorization を要求しなければなりません（MUST, §2.1）。その credential の管理・検証方法は RFC 7662 の scope 外です。

## 3. `active` は REQUIRED な Boolean である

RFC 7662 §2.2 では、Introspection Response の `active` member は REQUIRED です。値は、提示された token が現在 active かどうかを示す Boolean です。

`active: true` の具体的な判定は Authorization Server の実装と token に保持している情報に依存します。RFC 7662 は一般的な状態として、Authorization Server が token を発行していること、Resource Owner により revoke されていないこと、token の有効時間内であることを挙げています。

Response には `scope`、`client_id`、`username`、`token_type`、`exp`、`iat`、`nbf`、`sub`、`aud`、`iss`、`jti` などの OPTIONAL member も定義されています。

## 4. Authorization Server は適用可能な state check を行う

RFC 7662 §4 は、Protected Resource が Authorization Server に token state の判定を依存するため、Authorization Server は token state に対する適用可能なすべての check を実行しなければならない（MUST）と規定しています。

§4 が示す check は次のとおりです。

- token が expire し得る場合、expired かどうかを判定しなければならない（MUST）。
- token に使用開始時刻がある場合、その有効期間が開始しているかを判定しなければならない（MUST）。
- token が発行後に revoke され得る場合、revocation が行われたかを判定しなければならない（MUST）。
- token が署名されている場合、signature を検証しなければならない（MUST）。
- token が特定の Resource Server だけで使用できる場合、introspection request を行った Resource Server で使用可能かを判定しなければならない（MUST）。

RFC 7662 は、これらすべてがあらゆる OAuth 2.0 deployment に適用されるわけではなく、どの check が適用されるかは Authorization Server が判断するとしています。

<pre class="mermaid">
flowchart TD
    A[Protected Resource] --> B[token を POST]
    B --> C[Authorization Server]
    C --> D[適用可能な state check]
    D --> E{token は active か}
    E -->|Yes| F[active: true]
    E -->|No| G[active: false]
</pre>

## 5. inactive token は error response とは限らない

RFC 7662 §2.2 では、introspection call 自体が適切に authorized されていても、token が inactive、存在しない、または Protected Resource がその token を introspect することを許可されていない場合、Authorization Server は `active` を `false` とした Introspection Response を返さなければなりません（MUST）。

Authorization Server は inactive token について、なぜ inactive なのかを含む追加情報を response に含めるべきではありません（SHOULD NOT, §2.2）。§4 でも、Authorization Server の内部状態の開示を避けるため、required な `active: false` 以外の claim を含めるべきではない（SHOULD NOT）としています。

一方、Introspection Endpoint へのアクセスに使う credential が無効な場合は別です。RFC 7662 §2.3 は、Protected Resource が OAuth 2.0 client credentials で認証し、その credential が無効な場合には HTTP 401 を返すと規定しています。別の OAuth 2.0 bearer token で endpoint access を認可している場合も、その token の権限が不足しているか request に対して無効であれば HTTP 401 を返します。

つまり、introspection 対象 token の inactive state と、Introspection Endpoint へのアクセス自体の失敗は異なる処理です。

## 6. Response の cache と `exp`

RFC 7662 §2.2 は Protected Resource が Introspection Response を cache できる（MAY）としています。§4 は、cache による性能と token-state 情報の freshness の trade-off を system designer が考慮しなければならない（MUST）と規定しています。

Response に `exp` parameter が含まれる場合、その時刻を越えて response を cache してはなりません（MUST NOT, §4）。RFC 7662 は具体的な cache duration を一律には定めていません。

## 一次資料

- RFC Editor: [RFC 7662 — OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662.html)

参照した主要節: §2, §2.1, §2.2, §2.3, §4  
最終確認: 2026-09-19
