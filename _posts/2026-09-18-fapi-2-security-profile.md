---
layout: post
title: "FAPI 2.0 Security Profile：Authorization Code Flow の全体像"
date: 2026-09-18 09:20:00 +0900
categories: [authorization, api-security, fapi]
---

FAPI 2.0 Security Profile は、OpenID Foundation FAPI Working Group が策定した Final Specification です。

## この記事について

**記事タイプ:** Overview / Flow  
**対象読者:** FAPI 2.0 Security Profile に対応する Client、Authorization Server、Resource Server の実装者  
**この記事で伝えること:** FAPI 2.0 の Authorization Code Flow で、PAR、PKCE、issuer identification、Client Authentication、sender-constrained access token がどの順序で組み合わされるか  
**扱わないこと:** FAPI 2.0 Message Signing、OpenID Connect の ID Token 検証、個別の MTLS / DPoP 仕様詳細、FAPI 2.0 の全適合要件

この記事は FAPI 2.0 Security Profile の全条項を一覧化するものではありません。**Authorization Endpoint を利用するフローの全体像** に範囲を限定し、各処理がどこで必要になるかを仕様本文に沿って整理します。

## 1. FAPI 2.0 が組み合わせる仕様

FAPI 2.0 Security Profile §5.3.1 は、OAuth 2.0 と関連仕様を組み合わせて利用します。

このフローに関係する主な仕様は次のとおりです。

- **OAuth 2.0 Authorization Framework:** RFC 6749
- **Bearer Token Usage:** RFC 6750
- **PKCE:** RFC 7636
- **Mutual TLS:** RFC 8705
- **DPoP:** RFC 9449
- **Pushed Authorization Requests:** RFC 9126
- **Authorization Server Metadata:** RFC 8414
- **Authorization Server Issuer Identification:** RFC 9207
- **OpenID Connect:** OpenID Connect Core 1.0 incorporating errata set 1

FAPI 2.0 Security Profile は、これらの仕様にある選択肢をそのまま許容するのではなく、§5 で追加の適合要件を課します。

## 2. Authorization Code Flow の全体像

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    participant UA as User Agent
    C->>C: PKCE verifier / challenge を生成
    C->>AS: PAR + client authentication
    AS-->>C: request_uri + expires_in
    C->>UA: Authorization Request
    UA->>AS: client_id + request_uri
    AS-->>UA: authorization code + iss
    UA-->>C: redirect response
    C->>C: iss を検証
</pre>

Token Endpoint 以降は、次の処理になります。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    participant RS as Resource Server
    C->>AS: code + code_verifier + client authentication
    AS->>AS: code / PKCE / sender binding を検証
    AS-->>C: sender-constrained Access Token
    C->>RS: Access Token + MTLS または DPoP proof
    RS->>RS: token と sender constraint を検証
    RS-->>C: Protected Resource
</pre>

このフローでは、Authorization Request の主要パラメータをブラウザ経由で直接送るのではなく、最初に PAR endpoint へ送信します。その後、Authorization Endpoint、Token Endpoint、Resource Endpoint の順に処理が進みます。

## 3. PAR で Authorization Request を事前登録する

§5.3.2.2 は Authorization Server に、RFC 9126 に従う client-authenticated pushed authorization request のサポートを要求します。

Authorization Server は、PAR を使わずに送信された Authorization Request を拒否し、Client Authentication を伴わない PAR も拒否します。

Client は Authorization Endpoint に `client_id` と PAR で得た `request_uri` だけを送信しなければなりません（shall）。その他の Authorization Request parameter は PAR request に含めます。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    C->>AS: POST PAR endpoint + authorization parameters + client authentication
    AS->>AS: Client と request parameters を検証
    AS-->>C: request_uri + expires_in
    C->>AS: Authorization Request + client_id + request_uri
</pre>

PAR の `request_uri` に対して返す `expires_in` は600秒未満とすることが §5.3.2.2 に規定されています。

## 4. PKCE は S256 を使用する

Authorization Endpoint を使う場合、Authorization Server は PKCE を要求し、code challenge method は `S256` とします。

Client は Authorization Request ごとに PKCE challenge を生成し、その challenge を Client とフローを開始した User Agent に安全に結び付けます。

Token Request では、Client が authorization code と `code_verifier` を送信し、Authorization Server が PKCE の検証を行います。

## 5. Authorization Response の issuer を検証する

§5.3.2.2 は Authorization Server に、RFC 9207 の `iss` parameter を Authorization Response に含めることを要求します。

Client 側の §5.3.3.2 は、この `iss` を RFC 9207 に従って検証することを要求します。

この処理は、Authorization Response がどの Authorization Server から返されたものかを Client が確認する段階に位置します。

## 6. Token Endpoint では Client Authentication を行う

§5.3.2.1 は、FAPI 2.0 Security Profile の Authorization Server が confidential client のみをサポートし、Client Authentication に Mutual TLS または `private_key_jwt` を使用することを規定しています。

Token Request では、authorization code と `code_verifier` に加えて、選択した方式による Client Authentication が行われます。

Client Authentication は、次のいずれかの方式を使用します。

- **Mutual TLS:** RFC 8705
- **`private_key_jwt`:** RFC 7521 / RFC 7523 / OpenID Connect Core

## 7. Access Token は sender-constrained とする

Authorization Server は sender-constrained Access Token のみを発行します。方式は MTLS または DPoP です。

<pre class="mermaid">
flowchart TD
    C[Confidential Client] -->|Token Request + Client Authentication| AS[Authorization Server]
    AS -->|Sender-constrained Access Token| C
    C -->|Access Token + MTLS certificate / DPoP proof| RS[Resource Server]
    RS --> V1[Token validity / integrity / expiration / revocation]
    V1 --> V2[Authorization sufficiency]
    V2 --> V3[Sender constraint verification]
</pre>

Resource Server は §5.3.4 に従い、Access Token の validity、integrity、expiration、revocation status を検証し、要求された resource access に十分な authorization を表しているか確認します。そのうえで、MTLS または DPoP の sender constraint を検証します。

## 8. Authorization Code に関する要件

このフローでは Authorization Code 自体にも追加要件があります。

- Authorization Code の lifetime は最大60秒。
- 一度使用された Authorization Code は拒否する。
- DPoP を使用する場合、Authorization Server は Authorization Code Binding to DPoP Key をサポートする（shall）。Client にその利用までは要求されない。
- native application の loopback interface redirect を除き、`http` scheme の redirect URI を許可しない。

## 9. このフローを構成する要件の対応表

各処理段階と要件の対応は次のとおりです。

1. **Authorization Request の準備:** PKCE S256。
2. **Authorization Request の送信:** Client-authenticated PAR。
3. **Browser redirect:** `client_id` と `request_uri`。
4. **Authorization Response:** Authorization Code と `iss`。
5. **Client 側 response 検証:** RFC 9207 に従う issuer validation。
6. **Token Request:** Code、verifier、Client Authentication。
7. **Access Token 発行:** sender-constrained token。
8. **Resource access:** MTLS または DPoP による sender constraint verification。

## 10. この記事で扱っていない FAPI 2.0 の主題

FAPI 2.0 Security Profile には、このフロー以外にも network layer、metadata、refresh token、JWT algorithm、key length、OpenID Connect integration などの要件があります。これらは Authorization Code Flow の構成要素を把握するという本記事の範囲外です。

FAPI 2.0 Message Signing は別仕様であり、本記事では扱いません。

## 11. 一次資料

- OpenID Foundation: [FAPI 2.0 Security Profile](https://openid.net/specs/fapi-security-profile-2_0.html)
- RFC Editor: [RFC 9126 — OAuth 2.0 Pushed Authorization Requests](https://www.rfc-editor.org/rfc/rfc9126.html)
- RFC Editor: [RFC 9449 — OAuth 2.0 Demonstrating Proof of Possession](https://www.rfc-editor.org/rfc/rfc9449.html)
- RFC Editor: [RFC 8705 — OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens](https://www.rfc-editor.org/rfc/rfc8705.html)
- RFC Editor: [RFC 9207 — OAuth 2.0 Authorization Server Issuer Identification](https://www.rfc-editor.org/rfc/rfc9207.html)

参照した主要節: FAPI 2.0 Security Profile §5.3.1, §5.3.2.1, §5.3.2.2, §5.3.3.1, §5.3.3.2, §5.3.4  
最終確認: 2026-09-19
