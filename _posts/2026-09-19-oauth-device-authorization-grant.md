---
layout: post
title: "RFC 8628：Device Authorization Grant では user_code と device_code をどう使い分けるのか"
date: 2026-09-19 15:46:00 +0900
categories: [oauth, device]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** ブラウザや文字入力能力が制限された端末で OAuth 2.0 Device Authorization Grant を実装・レビューする開発者  
**この記事で伝えること:** Device Client が `device_code` と `user_code` を受け取り、利用者による別端末での承認と Token Endpoint の polling を経て Access Token を取得するまでの parameter 配置と処理順序  
**扱わないこと:** Authorization Code Grant、PKCE、端末固有の UI 設計、QR code の生成方法、個別 deployment の認可ポリシー

## 1. この flow では2種類の code が別の経路を通る

RFC 8628 は 2019 年 8 月公開の Proposed Standard で、適切な browser がない、または文字入力が制限された Internet-connected device 向けの OAuth 2.0 extension です。利用者は smartphone など別の device の user agent を使って authorization を完了します（RFC 8628 §1）。

中心となるのは `device_code` と `user_code` の役割の違いです。

- **`device_code`:** Device Client と Authorization Server の間で使う verification code。利用者に入力させる値ではない。
- **`user_code`:** 利用者が別端末の user agent で authorization session を識別するために使う code。

`device_code` は Token Endpoint の polling に使われ、`user_code` は利用者との interaction に使われます。

<pre class="mermaid">
flowchart TD
    A[Device Client] --> B[Device Authorization Endpoint]
    B --> C[device_code と user_code]
    C --> D[利用者へ verification_uri と user_code を表示]
    D --> E[別端末の User Agent]
    E --> F[利用者が承認または拒否]
    C --> G[device_code で Token Endpoint を polling]
    F --> G
    G --> H{Authorization の状態}
    H -->|pending| G
    H -->|approved| I[Access Token]
    H -->|denied / expired| J[Error]
</pre>

## 2. Device Authorization Endpoint に何を送るか

RFC 8628 §3.1 では、Client は Device Authorization Endpoint に HTTP POST request を送り、parameter を UTF-8 の `application/x-www-form-urlencoded` 形式で request entity-body に入れます。

`client_id` は Client が Authorization Server に対して認証していない場合に REQUIRED です。`scope` は OPTIONAL です。

次は構造を示すための非規範的な例です。

```http
POST /device_authorization HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded

client_id=device-client-123&scope=read%20profile
```

ここで `client_id` と `scope` は JSON member ではなく form parameter です。Confidential Client が client credentials を持つ場合、RFC 6749 §3.2.1 の Client authentication requirements が適用されます（RFC 8628 §3.1）。

Device からの request は TLS を使用し、BCP 195 の best practices を実装しなければなりません（MUST, RFC 8628 §3.1）。RFC 8628 本文が BCP 195 の参照先として挙げる RFC 7525 は RFC 9325 により obsolete されています。2026-09-22 時点の BCP 195 は RFC 8996、RFC 9325、RFC 9852 で構成されています。さらに、2026 年 7 月公開の RFC 10015 は RFC 9325 を更新し、(D)TLS 1.2 の obsolete な key exchange method を追加で deprecated / discouraged としているため、実装時は RFC 10015 を含む RFC 9325 の更新関係も確認します。

また、値のない parameter は request から省略されたものとして扱わなければならず（MUST）、Authorization Server は未知の request parameter を無視しなければなりません（MUST）。request / response parameter を複数回含めてはなりません（MUST NOT）。polling による不要な負荷を避けるため、Client は利用者に促された場合にのみ Device Authorization Request を開始し、application 起動時などに自動開始しないことが SHOULD です（RFC 8628 §3.1）。

## 3. Response object には2種類の code が入る

RFC 8628 §3.2 では、成功時に Authorization Server は HTTP 200 と `application/json` response を返します。

次は RFC 8628 が定義する構造を示す非規範的な例です。

```json
{
  "device_code": "device-code-value",
  "user_code": "ABCD-EFGH",
  "verification_uri": "https://authorization.example/device",
  "verification_uri_complete": "https://authorization.example/device?user_code=ABCD-EFGH",
  "expires_in": 1800,
  "interval": 5
}
```

各 member の役割は次のとおりです。

- **`device_code`:** REQUIRED。Device Client が Token Endpoint に提示する verification code。
- **`user_code`:** REQUIRED。利用者が扱う end-user verification code。
- **`verification_uri`:** REQUIRED。利用者が別端末の user agent で開く URI。
- **`verification_uri_complete`:** OPTIONAL。`user_code` 相当の情報を含む verification URI。
- **`expires_in`:** REQUIRED。`device_code` と `user_code` の lifetime を秒数で表す。
- **`interval`:** OPTIONAL。Token Endpoint への polling の最小間隔。省略された場合、Client は 5 秒を default として使用しなければなりません（MUST）。

## 4. 利用者には verification_uri と user_code を伝える

RFC 8628 §3.3 では、Client は成功した Device Authorization Response を受け取ると、`user_code` と `verification_uri` を利用者へ表示または伝達し、別端末の user agent で URI を開いて code を入力するよう案内します。

Authorization Server は、利用者が `verification_uri` へ移動し、interaction のどこかで `user_code` を提供する sequence を実装しなければなりません（MUST, §3.3）。そのほかの具体的な interaction sequence は Authorization Server に委ねられています。

`verification_uri_complete` が response に含まれる場合、Client は QR code や NFC など、browser をその URI で開く非テキスト方式を提示できます（MAY, §3.3.1）。ただし Client は `user_code` を引き続き表示しなければなりません（MUST）。

## 5. Device Client は device_code を Token Endpoint に送る

利用者との interaction と並行して、Device Client は Token Endpoint を polling します。RFC 8628 §3.4 では、`grant_type` を固定値 `urn:ietf:params:oauth:grant-type:device_code` にし、Device Authorization Response で得た `device_code` を送ります。

次は非規範的な HTTP request 例です。

```http
POST /token HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code&device_code=device-code-value&client_id=device-client-123
```

- **`grant_type`:** REQUIRED。値は `urn:ietf:params:oauth:grant-type:device_code` でなければならない（MUST）。
- **`device_code`:** REQUIRED。§3.2 で受け取った値。
- **`client_id`:** Client が Authorization Server に対して認証していない場合に REQUIRED。

Client credentials を発行されている Client は RFC 6749 §3.2.1 に従って Authorization Server に認証しなければなりません（MUST, RFC 8628 §3.4）。

`user_code` はこの Token Request には入りません。利用者向けの `user_code` と protocol 上の polling に使う `device_code` はここで明確に分離されています。

## 6. authorization_pending の間は polling を続ける

RFC 8628 §3.5 は Device Authorization Grant 固有の Token Endpoint error を定義しています。

`authorization_pending` は利用者の interaction がまだ完了していない状態です。Client は Access Token Request を繰り返すことが SHOULD ですが、各 request の前に Device Authorization Response の `interval` 秒以上、`interval` がなければ 5 秒以上待たなければなりません（MUST）。

`slow_down` を受け取った場合、Client はその request と以降の request について polling interval を 5 秒増加させなければなりません（MUST）。

`access_denied` は利用者が authorization request を拒否したことを表します。`expired_token` は `device_code` の有効期限が切れたことを表し、Client は Device Authorization Request を新たに開始できます（MAY）が、不要な polling を避けるため、再開前に利用者の操作を待つべきです（SHOULD）。

`authorization_pending` と `slow_down` 以外の error response を受け取った場合、Client は polling を停止しなければなりません（MUST）。また、connection timeout が発生した場合、Client は再試行前に自律的に polling 頻度を下げなければなりません（MUST）。その方法として、timeout ごとに polling interval を倍増するような exponential backoff が RECOMMENDED です。

利用者が grant を承認すると、Token Endpoint は RFC 6749 §5.1 の成功 response を返します（RFC 8628 §3.5）。

## 一次資料

- RFC Editor: [RFC 8628 — OAuth 2.0 Device Authorization Grant](https://www.rfc-editor.org/rfc/rfc8628.html)
- RFC Editor: [BCP 195 — Recommendations for Secure Use of TLS](https://www.rfc-editor.org/info/bcp195/)
- RFC Editor: [RFC 10015 — Deprecating Obsolete Key Exchange Methods in TLS 1.2 and DTLS 1.2](https://www.rfc-editor.org/rfc/rfc10015.html)

参照した主要節: RFC 8628 §1, §3.1, §3.2, §3.3, §3.3.1, §3.4, §3.5  
最終確認: 2026-09-22
