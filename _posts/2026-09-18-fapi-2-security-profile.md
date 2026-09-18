---
layout: post
title: "FAPI 2.0 Security Profile：PAR・PKCE・sender-constrained token の規範要件"
date: 2026-09-18 09:20:00 +0900
categories: [authorization, api-security, fapi]
---

FAPI 2.0 Security Profile は、OpenID Foundation FAPI Working Group が公開する Final Specification です。仕様は、自身を **general purpose high security profile of OAuth 2.0** と定義しています。

この仕様は OAuth 2.0、Bearer Token、PKCE、MTLS、DPoP、Pushed Authorization Requests (PAR)、Authorization Server Metadata、Authorization Server Issuer Identification、および OpenID Connect Core の一部を組み合わせ、Authorization Server、Client、Resource Server に追加要件を課します。

この記事では FAPI 2.0 Security Profile の規範要件を主体別に整理します。

## 1. 基礎となる仕様

FAPI 2.0 Security Profile §5.3.1 は、プロファイル対象として次の技術を列挙しています。

| 技術 | 参照仕様 |
|---|---|
| OAuth 2.0 Authorization Framework | RFC 6749 |
| OAuth 2.0 Bearer Token Usage | RFC 6750 |
| PKCE | RFC 7636 |
| OAuth 2.0 Mutual TLS | RFC 8705 |
| DPoP | RFC 9449 |
| Pushed Authorization Requests | RFC 9126 |
| OAuth 2.0 Authorization Server Metadata | RFC 8414 |
| OAuth 2.0 Authorization Server Issuer Identification | RFC 9207 |
| OpenID Connect Core | OpenID Connect Core 1.0 |

FAPI 2.0 の profile は、これらの仕様にある選択肢をそのまま許容するのではなく、§5 で適合要件を追加しています。

## 2. 全 endpoint に共通する network layer 要件

§5.2.1 は Client、Authorization Server、Resource Server に対し、次を規定します。

- TLS で保護された endpoint のみを提供し、他 server への接続にも TLS を使用する（shall）。
- TLS 1.2 以降を使用する（shall）。
- BCP 195 の Secure Use of Transport Layer Security の recommendation に従う（shall）。
- DNS spoofing 対策として DNSSEC を使用することが should とされている。
- RFC 9525 に従って TLS server certificate check を行う（shall）。

## 3. Authorization Server の一般要件

§5.3.2.1 では Authorization Server に次の要件が課されています。

| 項目 | 要件 |
|---|---|
| Metadata | OIDC Discovery / RFC 8414 に従って metadata を配布する |
| Resource Owner Password Credentials | request を拒否する |
| Client type | confidential client のみをサポートする |
| Access Token | sender-constrained access token のみを発行する |
| Sender constraint | MTLS または DPoP を使用する |
| Client Authentication | MTLS または `private_key_jwt` を使用する |
| Open redirector | 提供してはならない |
| Authorization Code lifetime | 最大60秒 |
| DPoP 使用時 | Authorization Code Binding to DPoP Key をサポートする |
| JWT clock offset | 0〜10秒未来の `iat` / `nbf` を受け入れ、60秒超の未来値は拒否する |

この profile では Authorization Server が refresh token rotation を security mechanism として通常利用することを認めておらず、§5.3.2.1 は extraordinary circumstances を除き refresh token rotation を使用しないことを shall としています。

## 4. Authorization Endpoint を使うフロー

Authorization Endpoint を利用する場合、§5.3.2.2 は `response_type=code`、client-authenticated PAR、PKCE S256 などを必須としています。

<pre class="mermaid">
sequenceDiagram
    participant C as Confidential Client
    participant AS as Authorization Server
    participant UA as User Agent
    participant RS as Resource Server
    C->>C: PKCE verifier/challenge を生成
    C->>AS: PAR + client authentication + redirect_uri + code_challenge(S256)
    AS->>AS: Client を認証し PAR を検証
    AS-->>C: request_uri + expires_in
    C->>UA: Authorization Request(client_id, request_uri)
    UA->>AS: client_id + request_uri
    AS->>UA: Resource Owner authentication / authorization
    AS-->>UA: authorization code + iss
    UA-->>C: redirect response
    C->>C: iss を検証
    C->>AS: Token Request + code + code_verifier + client authentication
    AS->>AS: code / PKCE / sender binding を検証
    AS-->>C: sender-constrained Access Token
    C->>RS: Access Token + MTLS または DPoP proof
    RS->>RS: token validity / authorization / sender constraint を検証
    RS-->>C: Protected Resource
</pre>

Authorization Server は次を行う必要があります。

1. `response_type` を `code` に限定する。
2. RFC 9126 に従う client-authenticated pushed authorization request をサポートする。
3. PAR を使わずに送られた authorization request を拒否する。
4. Client Authentication を伴わない PAR を拒否する。
5. PKCE を要求し、code challenge method は `S256` とする。
6. PAR に `redirect_uri` を要求する。
7. authorization response に RFC 9207 の `iss` parameter を返す。
8. native app の loopback interface redirect を除き、`http` scheme の redirect URI を許可しない。
9. 一度使用された authorization code を拒否する。
10. user credential を含む request を redirect する際、HTTP 307 status code を使用しない。
11. status code redirect では HTTP 303 を使用することが should とされている。
12. PAR の `request_uri` に対する `expires_in` を600秒未満とする。

## 5. Client の一般要件

§5.3.3.1 は Client に次の要件を課します。

- MTLS または DPoP の一方または両方を使う sender-constrained access token をサポートする。
- MTLS または `private_key_jwt` の一方または両方を使う Client Authentication をサポートする。
- Access Token は RFC 6750 §2.1 または DPoP §7.1 に従って HTTP header で送信する。
- open redirector を提供しない。
- `private_key_jwt` 使用時は Authorization Server の issuer identifier を `aud` claim に文字列として設定する。
- refresh token とその rotation をサポートする。
- MTLS 使用時は `mtls_endpoint_aliases` metadata をサポートする。
- DPoP 使用時は server provided nonce mechanism をサポートする。
- Authorization Server Metadata から取得した endpoint metadata のみを使用する。
- metadata 取得の基点となる issuer URL を authoritative source から secure channel で取得する。
- issuer URL と metadata の `issuer` が一致することを確認する。

Authorization Endpoint flow に関して §5.3.3.2 は、Client が Authorization Code Grant、PAR、PKCE S256 を使用すること、authorization request ごとに PKCE challenge を生成し Client と User Agent に安全に結び付けること、authorization response の `iss` を RFC 9207 に従って検証することを shall としています。

Authorization Endpoint に送信する request parameter は `client_id` と `request_uri` のみで、その他の authorization request parameter は PAR で送信します。

## 6. Sender-constrained Access Token

FAPI 2.0 Security Profile は Authorization Server に sender-constrained Access Token のみを発行することを要求し、方式として MTLS または DPoP を指定しています。

<pre class="mermaid">
flowchart LR
    C[Confidential Client] -->|Token Request + Client Authentication| AS[Authorization Server]
    AS -->|Sender-constrained Access Token| C
    C -->|Access Token + MTLS certificate / DPoP proof| RS[Resource Server]
    RS --> V1[Token validity / integrity / expiration / revocation]
    V1 --> V2[Authorization sufficiency]
    V2 --> V3[Sender constraint verification]
</pre>

## 7. Resource Server の要件

§5.3.4 は FAPI endpoint を持つ Resource Server に次の要件を課します。

1. Access Token を RFC 6750 §2.1 または DPoP §7.1 に従う HTTP header で受け入れる。
2. RFC 6750 §2.3 の query parameter による Access Token を受け入れない。
3. Access Token の validity、integrity、expiration、revocation status を検証する。
4. Access Token が表す authorization が要求された resource access に十分であることを検証する。
5. MTLS または DPoP による sender-constrained access token を検証する。

## 8. JWT と鍵に関する要件

§5.4.1 は cryptographic operation と secret に対し、次を規定します。

- JWT の作成・処理では RFC 8725 に従う。
- JWT algorithm は `PS256`、`ES256`、または Ed25519 variant の `EdDSA` を使用する。
- `none` algorithm を使用または受理しない。
- RSA key は2048 bit 以上。
- Elliptic Curve key は224 bit 以上。
- Access Token、Refresh Token、Authorization Code など end-user が扱うことを意図しない credential は少なくとも128 bit の entropy を持つよう作成する。

## 9. OpenID Connect との関係

仕様 §5.3.2.3 は、認証済みユーザーの identifier を token response で Client に提供する場合、Authorization Server が OpenID Connect をサポートすることを shall としています。

FAPI 2.0 Security Profile 自体は OAuth 2.0 の security profile であり、ユーザー identifier を返す必要がないケースでは OpenID Connect の利用は必須とは規定されていません。

## 10. 一次資料

- OpenID Foundation: [FAPI 2.0 Security Profile](https://openid.net/specs/fapi-security-profile-2_0.html)
- OpenID Foundation: [FAPI 2.0 Attacker Model](https://openid.net/specs/fapi-attacker-model-2_0-final.html)
- RFC Editor: [RFC 9126 — OAuth 2.0 Pushed Authorization Requests](https://www.rfc-editor.org/rfc/rfc9126.html)
- RFC Editor: [RFC 9449 — OAuth 2.0 Demonstrating Proof of Possession](https://www.rfc-editor.org/rfc/rfc9449.html)
- RFC Editor: [RFC 8705 — OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens](https://www.rfc-editor.org/rfc/rfc8705.html)
- RFC Editor: [RFC 9207 — OAuth 2.0 Authorization Server Issuer Identification](https://www.rfc-editor.org/rfc/rfc9207.html)

参照した主要節: FAPI 2.0 Security Profile §5.1.2, §5.2.1, §5.3.1, §5.3.2.1, §5.3.2.2, §5.3.2.3, §5.3.3.1, §5.3.3.2, §5.3.4, §5.4.1  
最終確認: 2026-09-18
