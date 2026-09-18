---
layout: post
title: "OpenID Connect Core：Authorization Code Flow で受け取る ID Token はどう検証するのか"
date: 2026-09-19 03:41:00 +0900
categories: [authentication, oidc]
---

OpenID Connect Core 1.0 incorporating errata set 2 は、Authorization Code Flow の Token Response で受け取った ID Token を Client が検証する手順を §3.1.3.7 に定義しています。

この記事では、§3.1.3.7 の検証手順だけでなく、その前提となる §2 の ID Token 要件も確認します。§3.1.3.7 だけを読んだ場合、`sub` と `iat` が REQUIRED Claim であることが見えにくいためです。

## この記事について

**記事タイプ:** Requirement  
**対象読者:** OpenID Connect の Authorization Code Flow を実装・レビューする Relying Party（Client）開発者  
**この記事で伝えること:** Token Endpoint から受け取った ID Token について、§2 と §3.1.3.7 に基づき、Client が確認する Claim・署名・暗号化の要件を整理する  
**扱わないこと:** Implicit Flow、Hybrid Flow、Self-Issued OpenID Provider、UserInfo Response、Access Token 自体の検証、Discovery や Dynamic Registration の手順

## 1. 対象仕様

本稿の対象は **OpenID Connect Core 1.0 incorporating errata set 2** です。

- **ステータス:** OpenID Final Specification incorporating errata set 2
- **公開日:** 2023-12-15
- **主な参照箇所:** §2, §3.1.3.3, §3.1.3.5–§3.1.3.7

Authorization Code Flow では、Client は Authorization Code を Token Endpoint に送り、成功した Token Response で ID Token と Access Token を受け取ります。§3.1.3.5 は、Client が Token Response を検証するとき、RFC 6749 の検証規則に加えて §3.1.3.7 の ID Token validation rules に従うことを MUST としています。

本稿では、そのうち ID Token の検証に焦点を当てます。

## 2. §3.1.3.7 の前提として、§2 の ID Token 要件を満たす必要がある

§3.1.3.7 は ID Token の検証手順を列挙していますが、ID Token 自体の内容は §2 で定義されています。

Authorization Code Flow で使用する ID Token では、少なくとも次の Claim が REQUIRED です。

- `iss`: Issuer Identifier
- `sub`: Subject Identifier
- `aud`: Audience
- `exp`: Expiration Time
- `iat`: Issued At

したがって、`sub` と `iat` も省略可能ではありません。§3.1.3.7 では `sub` に対する追加の比較規則は列挙されていませんが、`sub` Claim 自体は §2 により REQUIRED です。

また、ID Token は原則として JWS で署名され、暗号化する場合は「署名してから暗号化」した Nested JWT になります。Authorization Code Flow では、Client が Registration 時に明示的に `none` を要求した場合に限り、§2 が定める例外が適用されます。

## 3. 検証処理の全体像

<pre class="mermaid">
flowchart TD
    A[Token Response の ID Token] --> B{暗号化されているか}
    B -->|Yes| C[Client が Registration 時に指定した条件で復号]
    B -->|No| D[§2 の REQUIRED Claim を確認]
    C --> D
    D --> E[iss を検証]
    E --> F[aud を検証]
    F --> G[必要に応じて azp を検証]
    G --> H[署名と alg の条件を確認]
    H --> I[exp を検証し iat を確認]
    I --> J{Authentication Request で nonce を送ったか}
    J -->|Yes| K[nonce の存在と一致を確認]
    J -->|No| L[acr / auth_time の条件を確認]
    K --> L
</pre>

以下では、§3.1.3.7 の順序に沿って確認します。

## 4. 暗号化されている場合は、Client が指定した条件で復号する

ID Token が暗号化されている場合、Client は Registration 時に **Client 自身が指定した** 鍵とアルゴリズムを使用して復号します。

OpenID Connect Core §3.1.3.7 は、Registration 時に OP と暗号化を合意していたにもかかわらず ID Token が暗号化されていない場合、RP がその ID Token を拒否することを SHOULD としています。

暗号化された ID Token は §2 により Nested JWT であり、署名された ID Token を暗号化した構造です。

## 5. `iss` は期待する Issuer Identifier と完全一致させる

Client は、OpenID Provider の Issuer Identifier が ID Token の `iss` Claim と **完全一致**することを検証しなければなりません（MUST）。

Issuer Identifier は通常 Discovery によって取得されますが、Discovery の取得・検証手順自体は本稿の対象外です。

## 6. `aud` に Client 自身の `client_id` が含まれることを確認する

Client は、`aud` Claim に、`iss` で識別された Issuer に登録した自身の `client_id` が audience として含まれていることを検証しなければなりません（MUST）。

`aud` は複数の値を含む配列でも構いません（MAY）。ただし、次のいずれかに該当する場合、Client は ID Token を拒否しなければなりません（MUST）。

- `aud` に Client 自身が有効な audience として含まれていない
- Client が信頼しない追加 audience が含まれている

## 7. 複数 audience と `azp` を確認する

`azp`（authorized party）は OPTIONAL Claim です。

§3.1.3.7 は、`aud` に複数の audience が含まれる場合、Client が `azp` Claim の存在を確認することを SHOULD としています。

また、`azp` Claim が存在する場合、Client はその値が自身の `client_id` と一致することを確認することを SHOULD としています。

## 8. Authorization Code Flow では署名検証に例外がある

Authorization Code Flow の ID Token は、Token Endpoint から Client へ直接返されます。

§3.1.3.7 は、このように ID Token が Client と Token Endpoint の直接通信で受け取られる場合、トークン署名の検証に代えて TLS server validation によって Issuer を検証してもよい（MAY）としています。

それ以外の ID Token については、Client は JWT の `alg` Header Parameter で示されるアルゴリズムを用いて、JWS に従って署名を検証しなければなりません（MUST）。署名検証には Issuer が提供する鍵を使用しなければなりません（MUST）。

## 9. `alg` は既定値または Registration 時に指定した値であることを確認する

§3.1.3.7 は、`alg` の値について次のいずれかであることを SHOULD としています。

- 既定値の `RS256`
- Client が Registration 時に `id_token_signed_response_alg` で指定したアルゴリズム

MAC ベースの `HS256`、`HS384`、`HS512` を使用する場合、`aud` に含まれる `client_id` に対応する `client_secret` の UTF-8 表現のオクテット列を署名検証鍵として使用します。

MAC ベースのアルゴリズムで `aud` が複数値の場合の動作は、OpenID Connect Core では unspecified です。

## 10. `exp` は現在時刻より後でなければならない

Client は、現在時刻が `exp` Claim が表す時刻より前であることを確認しなければなりません（MUST）。

§2 は、実装が clock skew を考慮して数分程度の小さな許容幅を設けてもよい（MAY）としています。

一方、`iat` は §2 により REQUIRED Claim です。§3.1.3.7 は、発行時刻が現在時刻から離れすぎている ID Token を拒否するために `iat` を利用できるとしています。許容範囲は Client 固有です。

したがって、`iat` は「存在自体が任意」なのではなく、Claim は REQUIRED であり、その時刻に対してどの範囲を許容するかが Client 固有です。

## 11. Authentication Request で `nonce` を送った場合は一致を確認する

Authentication Request に `nonce` を含めた場合、ID Token に `nonce` Claim が存在しなければならず、その値が Authentication Request で送った値と同一であることを確認しなければなりません（MUST）。

Client は `nonce` の replay attack も確認することが SHOULD とされています。ただし、replay detection の具体的な方法は Client 固有です。

Authorization Code Flow では `nonce` request parameter 自体は OPTIONAL ですが、送信した場合にはこの検証が必須になります。

## 12. `acr` と `auth_time` は要求した場合に確認する

`acr` Claim を要求した場合、Client は返された Claim Value が適切であることを確認することを SHOULD とされています。どの `acr` 値を適切と判断するか、その意味と処理は OpenID Connect Core のこの節では規定されていません。

`auth_time` Claim を個別に要求した場合、または `max_age` parameter を使用した場合、Client は `auth_time` を確認し、最後の End-User authentication から時間が経過しすぎていると判断した場合に再認証を要求することを SHOULD とされています。

なお、`max_age` を使用した場合、§3.1.2.1 により OP は ID Token に `auth_time` Claim を含めなければなりません（MUST）。

## 13. 検証対象をまとめる

Authorization Code Flow の Token Response で受け取る ID Token について、Client が確認する主な項目は次のとおりです。

1. 暗号化されている場合は、Client が Registration 時に指定した鍵とアルゴリズムで復号する。
2. §2 で REQUIRED とされる `iss`、`sub`、`aud`、`exp`、`iat` が ID Token の要件を満たしていることを確認する。
3. `iss` が期待する Issuer Identifier と完全一致することを確認する（MUST）。
4. `aud` に自身の `client_id` が含まれることを確認する（MUST）。
5. `aud` が複数値なら `azp` の存在を確認し（SHOULD）、`azp` が存在する場合は自身の `client_id` と一致することを確認する（SHOULD）。
6. §3.1.3.7 が定める条件に従って署名を検証し、`alg` の条件を確認する。
7. `exp` を検証する（MUST）。`iat` は REQUIRED Claim であり、必要に応じて許容時刻範囲を確認する。
8. Authentication Request で `nonce` を送った場合、その存在と一致を確認する（MUST）。
9. 要求した場合は `acr` と `auth_time` を確認する。

この整理は Authorization Code Flow の ID Token validation に限定したものです。Implicit Flow と Hybrid Flow では、それぞれ追加要件または異なる検証規則があります。

## 14. 一次資料

- OpenID Foundation: [OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)

参照した主要節: §2, §3.1.2.1, §3.1.3.3, §3.1.3.5–§3.1.3.7  
最終確認: 2026-09-19
