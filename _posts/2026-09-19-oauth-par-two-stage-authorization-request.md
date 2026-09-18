---
layout: post
title: "RFC 9126：PAR で Authorization Request はどのように2段階化されるか"
date: 2026-09-19 01:46:00 +0900
categories: [authorization, oauth]
---

OAuth 2.0 Pushed Authorization Requests（PAR）は RFC 9126 で定義されています。この記事では、Authorization Request のデータを先に Authorization Server へ直接送信し、その後 User Agent を経由して `request_uri` を Authorization Endpoint へ渡す、2段階の処理に範囲を限定します。

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth Client / Authorization Server の PAR 実装・レビューを担当する開発者  
**この記事で伝えること:** PAR Endpoint への pushed authorization request と、その応答で得た `request_uri` を使う Authorization Request の処理順序  
**扱わないこと:** JAR の署名・暗号化処理、PKCE の詳細、Authorization Code の交換、Access Token の利用、FAPI 2.0 固有の追加要件

## 1. PAR Endpoint へ Authorization Request を push する

RFC 9126 §2 は、Authorization Server に Pushed Authorization Request Endpoint を定義します。この endpoint は HTTPS を使用しなければなりません（MUST）。Client は Authorization Request を構成する parameter を、この endpoint へ HTTP `POST` で直接送信します。

§2.1 によれば、pushed authorization request には `client_id`、`response_type`、`redirect_uri`、`scope`、`state`、`code_challenge` など、Authorization Endpoint に適用可能な parameter を含めることができます。ただし `request_uri` parameter は含めてはなりません（MUST NOT）。

Client Authentication が必要な Client は、Token Endpoint request と同じ規則に従って認証情報も送信します。Authorization Server は §2.1 の処理として Client を認証し、`request_uri` parameter が送信されていれば request を拒否し、pushed request を Authorization Request として検証します。

## 2. 成功すると `request_uri` が返る

RFC 9126 §2.2 では、検証に成功した Authorization Server は request URI を生成し、HTTP `201` response で返さなければなりません（MUST）。response body には `request_uri` と `expires_in` が含まれます。

`request_uri` は、push された Authorization Request のデータを後続の Authorization Request から参照するための値です。§2.2 は、この値を push を行った Client に binding しなければならない（MUST）と規定しています。

この段階では User Agent は処理に参加しません。Client と Authorization Server の直接通信です。

## 3. User Agent を経由する Authorization Request

Client は取得した `request_uri` を使い、User Agent を Authorization Endpoint へ送ります。RFC 9126 §4 の例では、Authorization Endpoint への request は `client_id` と `request_uri` を含みます。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    participant UA as User Agent
    C->>AS: POST PAR Endpoint<br/>Authorization Request parameters
    AS->>AS: Client と request を検証
    AS-->>C: 201 + request_uri + expires_in
    C->>UA: Authorization Endpoint へ遷移
    UA->>AS: client_id + request_uri
    AS->>AS: pushed request を参照・検証
</pre>

このため、PAR の基本フローは次の2段階に分かれます。

1. **PAR への直接送信:** Client が Authorization Request のデータを PAR Endpoint へ直接 push し、`request_uri` を取得する。
2. **Authorization Endpoint への送信:** Client が User Agent を経由して `client_id` と `request_uri` を Authorization Endpoint へ送る。

## 4. `request_uri` の利用条件

RFC 9126 §4 は、Client が `request_uri` を1回だけ使用しなければならない（MUST）と規定しています。Authorization Server は `request_uri` を one-time use として扱うべきです（SHOULD）が、User Agent の reload / refresh による重複 request を許可してもよい（MAY）とされています。

期限切れの `request_uri` は invalid として拒否しなければなりません（MUST）。

Authorization Server は pushed request から生じた Authorization Request を、通常の Authorization Request と同様に検証しなければなりません（MUST）。push 時にすでに実施した検証については、request が pushed request であること、および検証結果に影響する request や policy の変更がないことを確認できる場合、Authorization Endpoint で省略してもよい（MAY）とされています。

## 5. PAR が変えるのは Authorization Request の渡し方

RFC 9126 がこのフローで追加する中心的な要素は、Authorization Request のデータを最初から User Agent 経由で Authorization Endpoint へ渡すのではなく、Client から Authorization Server へ直接 push して参照値を取得する処理です。

<pre class="mermaid">
flowchart TD
    A[Authorization Request parameters] --> B[PAR Endpoint へ POST]
    B --> C[Authorization Server が検証]
    C --> D[request_uri を発行]
    D --> E[User Agent を Authorization Endpoint へ送る]
    E --> F[client_id + request_uri]
    F --> G[pushed request を参照]
</pre>

Authorization Code の発行や Token Endpoint での code exchange は、この2段階の Authorization Request より後の処理であり、この記事の対象外です。

## 6. 一次資料

- RFC Editor: [RFC 9126 — OAuth 2.0 Pushed Authorization Requests](https://www.rfc-editor.org/rfc/rfc9126.html)

参照した主要節: §2, §2.1, §2.2, §4  
最終確認: 2026-09-19
