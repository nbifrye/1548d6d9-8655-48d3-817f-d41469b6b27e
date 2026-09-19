---
layout: post
title: "RFC 8705 / RFC 9449：mTLS と DPoP では sender-constrained Access Token をどう検証するのか"
date: 2026-09-20 05:39:00 +0900
categories: [oauth, mtls, dpop, access-token]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** sender-constrained Access Token を実装・レビューする OAuth Client / Authorization Server / Resource Server 開発者  
**この記事で伝えること:** RFC 8705 の mutual-TLS certificate-bound Access Token と RFC 9449 の DPoP-bound Access Token について、token が何に結び付けられ、protected resource request で Resource Server がその binding をどのように検証するか  
**扱わないこと:** どちらの方式を採用すべきかという評価、mutual-TLS Client Authentication、DPoP nonce、authorization code と DPoP key の binding、FAPI profile 固有の要求

## Article brief

- **Reader:** OAuth Client / Authorization Server / Resource Server の実装者
- **Question:** mTLS と DPoP は、Access Token の sender constraint をそれぞれ何に結び付け、Resource Server で何を照合するのか
- **Answer:** mTLS では Client certificate、DPoP では DPoP public key が binding の対象となり、Resource Server で proof of possession を確認する位置と HTTP 上の表現が異なることを説明できる
- **Scope:** RFC 8705 §3–§3.2 と RFC 9449 §3、§4、§6、§7–§7.1 に定義された Access Token の sender constraint と protected resource access
- **Out of scope:** 方式選定、性能・運用評価、RFC 8705 §2 の Client Authentication、RFC 9449 §8 の nonce、refresh token、FAPI profile 固有要件
- **Primary sources:** RFC 8705 §3–§3.2、RFC 9449 §3、§4、§6、§7–§7.1
- **Diagram:** token binding と protected resource request における検証対象を、mTLS と DPoP の2経路で示す縦方向 flowchart

## 1. 共通する目的は Access Token を鍵の所持者に制約すること

RFC 8705 の mutual-TLS client certificate-bound Access Token と RFC 9449 の DPoP-bound Access Token は、いずれも Access Token を単なる bearer token として扱わず、対応する private key を利用できる主体に token の利用を制約します（RFC 8705 §1、RFC 9449 §2）。

ただし、binding の対象と proof of possession を確認する層は同じではありません。

- **mTLS:** Access Token を、Token Endpoint への mutual TLS connection で Client が使用した X.509 certificate に結び付けます（RFC 8705 §3）。protected resource request でも同じ certificate を使った mutual TLS connection が必要です。
- **DPoP:** Access Token を、DPoP proof に示された public key に結び付けます（RFC 9449 §3、§6）。protected resource request では Client がその request 用の DPoP proof JWT を作成し、対応する private key の所持を示します。

<pre class="mermaid">
flowchart TD
    A[Access Token の sender constraint]
    A --> M[mTLS]
    M --> MC[Client certificate に binding]
    MC --> MT[TLS layer の certificate と照合]
    A --> D[DPoP]
    D --> DK[DPoP public key に binding]
    DK --> DP[DPoP proof の public key と照合]
</pre>

この図は2仕様の binding と照合対象だけを示した非規範的な整理です。

## 2. mTLS は Client certificate に Access Token を結び付ける

RFC 8705 §3 では、Client が Token Endpoint への connection で mutual TLS を使用すると、Authorization Server は発行する Access Token を Client certificate に結び付けられます。binding の情報は、JWT Access Token に certificate hash を含める方法や Token Introspection で Resource Server に伝える方法などで利用できます。

JWT で Access Token を表現する場合、RFC 8705 §3.1 は certificate の SHA-256 thumbprint を `cnf` claim 内の `x5t#S256` member で表すことを SHOULD としています。

次は構造だけを示す非規範的な最小例です。`x5t#S256` の値は illustrative value です。

```json
{
  "cnf": {
    "x5t#S256": "illustrative-certificate-thumbprint"
  }
}
```

`x5t#S256` は、X.509 certificate の DER encoding に対する SHA-256 hash を base64url encode した値です。RFC 8705 §3.1 は、その base64url value について末尾の `=` padding を省略しなければならず（MUST）、改行・空白・その他の追加文字を含めてはならない（MUST NOT）としています。

## 3. mTLS の protected resource request では TLS layer の certificate を照合する

RFC 8705 §3 は、certificate-bound Access Token を使用する protected resource request を、Token Endpoint で使用したものと同じ certificate による mutually authenticated TLS connection 上で行わなければならない（MUST）としています。

Resource Server は TLS implementation layer から Client certificate を取得しなければならず（MUST）、その certificate が Access Token に関連付けられた certificate と一致することを検証しなければなりません（MUST）。一致しない場合は、HTTP `401` と `invalid_token` を使って request を拒否しなければなりません（MUST）（RFC 8705 §3）。

次は HTTP 上の配置を示す非規範的な例です。Client certificate は HTTP header に格納される parameter ではなく、mutual TLS connection で提示されます。

```http
GET /resource HTTP/1.1
Host: resource.example
Authorization: Bearer illustrative-access-token
```

この request を処理するとき、Resource Server が照合する proof-of-possession 情報は TLS layer から取得した Client certificate です。

## 4. DPoP は DPoP public key に Access Token を結び付ける

RFC 9449 §3 では、Client は Token Request に DPoP proof JWT を `DPoP` HTTP header field で付加します。Authorization Server は Access Token を、その proof で Client が示した public key に結び付けます。

Resource Server は、Access Token が DPoP-bound かを確実に識別し、DPoP proof の public key との binding を検証するために十分な情報を取得できなければなりません（MUST）（RFC 9449 §6）。また、DPoP をサポートする Resource Server は、DPoP proof の public key が Access Token に結び付けられた public key と一致することを保証しなければなりません（MUST）。

JWT Access Token では、RFC 9449 §6.1 が `cnf` claim 内の `jkt` member を定義しています。`jkt` の値は、binding 対象の DPoP public key の JWK SHA-256 Thumbprint を base64url encode した値でなければなりません（MUST）。

次は構造だけを示す非規範的な最小例です。`jkt` の値は illustrative value です。

```json
{
  "cnf": {
    "jkt": "illustrative-jwk-thumbprint"
  }
}
```

## 5. DPoP の protected resource request では request ごとの proof を検証する

RFC 9449 §7 は、DPoP-protected resource への request に DPoP proof と Access Token の両方を含めなければならない（MUST）としています。proof は `DPoP` HTTP header field に置き、DPoP-bound Access Token は `Authorization` header field で `DPoP` authentication scheme を使って送ります（§7.1）。

次は配置を示す非規範的な例です。JWT と token の値は illustrative value です。

```http
GET /resource HTTP/1.1
Host: resource.example
Authorization: DPoP illustrative-access-token
DPoP: illustrative.dpop.proof
```

protected resource request の DPoP proof は `ath` claim を含み、その値は関連する Access Token の有効な hash でなければなりません（MUST）（RFC 9449 §7）。Resource Server は提示された token value の hash を計算し、`ath` と一致することを検証します。

さらに Resource Server は、DPoP proof を RFC 9449 §4.3 の規則に従って検証し、proof の public key が Access Token に binding された public key と一致することを確認しなければなりません（MUST）（§7.1）。すべての検証が成功しない限り resource への access を許可してはなりません（MUST NOT）。

## 6. proof of possession を確認する場所が異なる

mTLS では、Client が certificate に対応する private key を所持していることの proof は mutual TLS handshake に含まれます。RFC 8705 §1.2 は、mutual TLS を Client が X.509 certificate を提示し、TLS session の negotiation 中に対応する private key の所持を証明する処理として定義しています。protected resource では Resource Server が TLS layer から certificate を取得し、Access Token の binding と照合します。

DPoP では、proof of possession は application layer の DPoP proof JWT として各 HTTP request に付加されます。RFC 9449 §4 は各 HTTP request に一意な DPoP proof が必要であるとし、有効な proof はその JWT の署名に使われた private key を Client が所持していることを示します。

**The binding target differs: mTLS binds the token to an X.509 certificate, while DPoP binds it to a public key represented through the DPoP proof.**  
（binding の対象は異なります。mTLS は token を X.509 certificate に結び付け、DPoP は DPoP proof を通じて示される public key に結び付けます。）

この違いは仕様上の処理位置とデータ構造の違いを示すものであり、どちらを採用すべきかという評価ではありません。

## 7. Client Authentication とは分けて考える

RFC 8705 は mutual-TLS Client Authentication と certificate-bound Access Token を別の mechanism として定義しており、両者は必ずしも一緒に使用する必要はありません（RFC 8705 §1）。

RFC 9449 §3 も DPoP は Client Authentication method ではないと明記しています。DPoP は public client でも利用でき、`private_key_jwt` その他の Client Authentication method と組み合わせられるよう設計されています。

したがって本記事で比較しているのは Client Authentication method ではなく、Access Token の sender constraint と protected resource request での binding verification です。

## 一次資料

- RFC 8705, *OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens*, §1、§1.2、§3–§3.2  
  https://www.rfc-editor.org/rfc/rfc8705.html
- RFC 9449, *OAuth 2.0 Demonstrating Proof of Possession (DPoP)*, §2–§4、§6–§7.1  
  https://www.rfc-editor.org/rfc/rfc9449.html
