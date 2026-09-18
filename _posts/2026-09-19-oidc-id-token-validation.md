---
layout: post
title: "OpenID Connect Core：Authorization Code Flow の ID Token はどう検証するのか"
date: 2026-09-19 03:41:00 +0900
categories: [authentication, oidc]
---

OpenID Connect Core 1.0 incorporating errata set 2 は、Authorization Code Flow の Token Response で受け取った ID Token を Client が検証する手順を §3.1.3.7 に定義しています。

## この記事について

**記事タイプ:** Requirement  
**対象読者:** OpenID Connect の Authorization Code Flow を実装・レビューする Relying Party（Client）開発者  
**この記事で伝えること:** Token Endpoint から受け取った ID Token について、Client が §3.1.3.7 で要求される検証をどの順序で行うか  
**扱わないこと:** Implicit Flow、Hybrid Flow、Self-Issued OpenID Provider、UserInfo Response、Access Token 自体の検証、Discovery や Dynamic Registration の手順

## Article brief

- **Reader:** Authorization Code Flow の ID Token 検証を実装する RP 開発者
- **Question:** Token Response の ID Token に対し、どの値をどの順序で検証する必要があるか
- **Answer:** §3.1.3.7 の検証手順と、各 Claim・署名・暗号化に対する規範要件を区別できる
- **Scope:** OpenID Connect Core 1.0 incorporating errata set 2 §3.1.3.5–§3.1.3.7
- **Out of scope:** 他の Flow、Access Token validation、Discovery、Registration の詳細
- **Primary sources:** OpenID Connect Core 1.0 incorporating errata set 2
- **Diagram:** Token Response 受領後の ID Token validation を縦方向の flowchart で示す

## 1. Authorization Code Flow では ID Token は Token Endpoint から返る

Authorization Code Flow では、Client は Authorization Code を Token Endpoint に送り、Token Response を受け取ります。OpenID Connect Core §3.1.3.3 は、成功した Token Response に ID Token と Access Token が含まれることを規定しています。

§3.1.3.5 では、Client は Token Response を検証するとき、RFC 6749 の検証規則に加えて、§3.1.3.7 の ID Token validation rules に従わなければならない（MUST）としています。

この記事では、そのうち ID Token の検証だけを扱います。

## 2. 検証処理の全体像

<pre class="mermaid">
flowchart TD
    A[Token Response の ID Token] --> B{暗号化されているか}
    B -->|Yes| C[登録時の鍵とアルゴリズムで復号]
    B -->|No| D[Issuer と Audience を検証]
    C --> D
    D --> E[署名と alg を検証]
    E --> F[exp を検証]
    F --> G{nonce を送ったか}
    G -->|Yes| H[nonce を照合]
    G -->|No| I[追加 Claim の条件を確認]
    H --> I
</pre>

この図は §3.1.3.7 の処理を要約したものです。以下では、仕様に記載された順序に沿って確認します。

## 3. 暗号化されている場合は最初に復号する

§3.1.3.7 の最初の手順は ID Token の暗号化に関するものです。

ID Token が暗号化されている場合、Client は Registration 時に OP が ID Token の暗号化に使用すると指定した鍵とアルゴリズムを使用して復号します。

暗号化を OP と Registration 時に合意していたにもかかわらず ID Token が暗号化されていない場合、RP はその ID Token を拒否することが SHOULD とされています。

## 4. `iss` は期待する Issuer Identifier と完全一致させる

次に Client は `iss` Claim を検証します。

§3.1.3.7 は、OpenID Provider の Issuer Identifier が ID Token の `iss` Claim と **exactly match** しなければならない（MUST）と規定しています。

Issuer Identifier は通常 Discovery によって取得されますが、Discovery の取得・検証手順自体はこの記事の対象外です。

## 5. `aud` に Client 自身の `client_id` が含まれることを確認する

Client は `aud` Claim に、`iss` で識別された Issuer に登録した自身の `client_id` が audience として含まれていることを検証しなければなりません（MUST）。

`aud` は複数要素の配列でも構いません（MAY）。ただし、Client が有効な audience として列挙されていない場合、または Client が信頼しない追加 audience が含まれる場合、ID Token は拒否されなければなりません（MUST）。

## 6. `azp` が存在する場合の扱い

§3.1.3.7 は `azp`（authorized party）について、extension によって `azp` Claim が存在する場合、その extension の規則に従って値を検証することを SHOULD としています。

また `azp` が存在するとき、Client が Claim Value と自身の `client_id` の一致を確認することを SHOULD とする検証を含めてもよい（MAY）としています。

ここでの extension 固有の意味や処理は OpenID Connect Core のこの節の範囲外です。

## 7. 署名を検証する

Authorization Code Flow の ID Token は Token Endpoint と Client の直接通信で受け取ります。§3.1.3.7 は、この場合 TLS server validation を token signature の検証に代えて issuer validation に使用してもよい（MAY）としています。

一方、その他の ID Token については、Client は JWT の `alg` Header Parameter で指定されたアルゴリズムを使い、JWS に従って署名を検証しなければなりません（MUST）。また、Client は Issuer が提供する鍵を使用しなければなりません（MUST）。

`alg` は、既定の `RS256` または Registration 時に Client が `id_token_signed_response_alg` で送ったアルゴリズムであることが SHOULD とされています。

MAC ベースの `HS256`、`HS384`、`HS512` を使う場合、§3.1.3.7 は `aud` に含まれる `client_id` に対応する `client_secret` の UTF-8 表現の octets を署名検証鍵として使用すると規定しています。`aud` が複数値の場合の MAC ベースアルゴリズムの動作は unspecified です。

## 8. `exp` は現在時刻より後でなければならない

Client は現在時刻が `exp` Claim の時刻より前であることを確認しなければなりません（MUST）。

`iat` Claim は、発行時刻が現在時刻から離れすぎた token を拒否するために利用できます。許容する時間範囲は Client specific とされています。

したがって §3.1.3.7 は `exp` について MUST の検証を規定する一方、`iat` の許容範囲について共通の固定値を規定していません。

## 9. Authentication Request で `nonce` を送った場合は一致を確認する

Authentication Request に `nonce` を含めた場合、ID Token に `nonce` Claim が存在しなければならず、その値が Authentication Request で送った値と同一であることを確認しなければなりません（MUST）。

Client は `nonce` の replay attack も確認することが SHOULD とされています。ただし replay detection の正確な方法は Client specific です。

## 10. `acr` と `auth_time` は要求した場合に確認する

`acr` Claim を要求した場合、Client は assertion された Claim Value が適切であることを確認することが SHOULD とされています。ただし `acr` Claim Value の意味と処理は、この仕様の対象外です。

`auth_time` Claim を個別に要求した場合、または `max_age` parameter を使用した場合、Client は `auth_time` を確認し、最後の End-User authentication から時間が経過しすぎたと判断したときは再認証を要求することが SHOULD とされています。

## 11. §3.1.3.7 の検証対象をまとめる

Authorization Code Flow の Token Response で受け取る ID Token に対して、Client が確認する対象は次のように整理できます。

1. 暗号化されている場合は、合意した鍵とアルゴリズムで復号する。
2. `iss` が期待する Issuer Identifier と完全一致することを確認する（MUST）。
3. `aud` に自身の `client_id` が含まれることを確認する（MUST）。
4. `azp` が存在する場合は、適用される条件に従って確認する。
5. §3.1.3.7 が規定する条件に従って署名を検証する。
6. `alg` を確認する。
7. `exp` が現在時刻より後であることを確認する（MUST）。
8. 必要に応じて `iat` を利用する。
9. Authentication Request で `nonce` を送った場合、その存在と一致を確認する（MUST）。
10. 要求した場合は `acr` と `auth_time` を確認する。

この手順は Authorization Code Flow の ID Token validation に限定したものです。Implicit Flow と Hybrid Flow では、それぞれ別の節に追加要件と検証規則があります。

## 12. 一次資料

- OpenID Foundation: [OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)

参照した主要節: §3.1.3.3, §3.1.3.5, §3.1.3.7  
最終確認: 2026-09-19
