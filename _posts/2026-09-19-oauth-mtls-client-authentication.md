---
layout: post
title: "RFC 8705：Mutual-TLS Client Authentication では証明書をどう Client に結び付けるのか"
date: 2026-09-19 18:43:00 +0900
categories: [oauth, mtls]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 の Authorization Server で mutual-TLS Client Authentication を実装・レビューする開発者  
**この記事で伝えること:** RFC 8705 が定義する PKI Mutual-TLS Method と Self-Signed Certificate Mutual-TLS Method で、Client が提示した X.509 certificate を `client_id` に対応する credential としてどのように検証するか  
**扱わないこと:** certificate-bound Access Token、Resource Server での proof-of-possession、`cnf` / `x5t#S256`、`mtls_endpoint_aliases`、TLS 自体の handshake 詳細

RFC 8705 は、2020年2月に公開された Proposed Standard（Standards Track）です。

## 1. Mutual-TLS Client Authentication の位置

RFC 8705 §2 は、OAuth 2.0 の Client Authentication を X.509 client certificate を用いて行う2つの方式を定義しています。

- PKI Mutual-TLS Method
- Self-Signed Certificate Mutual-TLS Method

Authorization Server が特定 Client に mutual TLS authentication を要求するかどうかは、policy または Client configuration によって決まります。

この2方式を利用する request では、Client と Authorization Server の TLS connection が mutual-TLS X.509 certificate authentication により確立または再確立されていなければなりません（MUST, §2）。

<pre class="mermaid">
flowchart TD
    A[Client] --> B[mutual TLS connection]
    B --> C[Client certificate を提示]
    C --> D[OAuth request に client_id]
    D --> E[Authorization Server]
    E --> F{登録済み credential と一致するか}
    F -->|Yes| G[Client authentication 成功]
    F -->|No| H[invalid_client]
</pre>

## 2. `client_id` は OAuth request に含める

RFC 8705 §2 では、mutual-TLS Client Authentication を使用する Authorization Server へのすべての request で、Client は OAuth 2.0 の `client_id` parameter を含めなければなりません（MUST）。

`client_id` は X.509 certificate の field そのものではありません。Authorization Server は `client_id` から Client configuration を特定し、TLS handshake で提示された certificate を、その Client に期待される credential と照合します。

次は Token Endpoint で mutual-TLS Client Authentication を使用する場合の、構造を示すための非規範的な例です。

```http
POST /token HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE_VALUE&
client_id=client-123
```

この HTTP body に X.509 certificate を parameter として入れるわけではありません。certificate は mutual TLS connection の TLS handshake で Client から Server に提示されます。一方、`client_id` は OAuth request parameter として送られます。

Authorization Server は Client と certificate の binding を RFC 8705 §2.1 または §2.2 の方式で強制しなければなりません（MUST）。certificate が提示されない場合、または提示された certificate が `client_id` に期待されるものと一致しない場合、Authorization Server は OAuth 2.0 error response の `invalid_client` を返します。

## 3. PKI Mutual-TLS Method

RFC 8705 §2.1 の PKI Mutual-TLS Method は、validated certificate chain と、Client ごとに設定または登録された単一の subject distinguished name（DN）または単一の subject alternative name（SAN）を用います。

TLS handshake は、Client が certificate の public key に対応する private key を保持していること、および certificate chain の検証に使用されます。

Client authentication が成功するのは、certificate の subject information が、その Client に設定または登録された単一の expected subject と一致する場合です。

RFC 8705 は Client metadata として、たとえば次の値を定義しています。

```json
{
  "token_endpoint_auth_method": "tls_client_auth",
  "tls_client_auth_subject_dn": "CN=client.example"
}
```

これは構造を示すための非規範的な例です。

- `token_endpoint_auth_method`: Token Endpoint で使用する Client Authentication method。PKI Mutual-TLS Method の値は `tls_client_auth`。
- `tls_client_auth_subject_dn`: Client が使用する certificate に期待される subject distinguished name の string。

RFC 8705 §2.1.2 は subject DN のほか、SAN の DNS name、URI、IP address、email address を指定する metadata parameter も定義しています。`tls_client_auth` を使用する Client は、これらの metadata parameter のうち正確に1つを使用して、Authorization Server が認証時に期待する certificate subject value を示さなければなりません（MUST）。

certificate の revocation status を検査するかどうか、およびその方法は Authorization Server の deployment decision です。

## 4. Self-Signed Certificate Mutual-TLS Method

RFC 8705 §2.2 の Self-Signed Certificate Mutual-TLS Method では、Client は事前に X.509 certificate を Authorization Server に登録します。

登録には RFC 7591 の `jwks`、または Client の JWK Set を参照する `jwks_uri` を使用します。certificate は JWK の `x5c` parameter で表されます。

構造を示すための非規範的な Client metadata 例は次のとおりです。

```json
{
  "token_endpoint_auth_method": "self_signed_tls_client_auth",
  "jwks": {
    "keys": [
      {
        "kty": "EC",
        "crv": "P-256",
        "x": "PUBLIC_KEY_X_VALUE",
        "y": "PUBLIC_KEY_Y_VALUE",
        "x5c": ["BASE64_DER_CERTIFICATE_VALUE"]
      }
    ]
  }
}
```

この例では次のように配置されます。

- `token_endpoint_auth_method`: top-level Client metadata member。値は `self_signed_tls_client_auth`。
- `jwks`: top-level Client metadata member。JWK Set object。
- `keys`: JWK Set 内の JWK array。
- `x5c`: 個々の JWK 内の certificate chain を表す array。

Self-Signed Certificate Method では、TLS により Client が certificate の public key に対応する private key を保持していることを検証します。一方、PKI Method と異なり、Authorization Server は Client certificate chain を検証しません。提示された certificate が、その Client に設定または登録された certificate の1つと一致すれば Client authentication は成功します。

## 5. 2つの方式で何を照合するか

PKI Method では、Authorization Server は validated certificate chain を前提として、certificate の subject DN または SAN を Client に登録された expected subject と照合します。

Self-Signed Certificate Method では、Authorization Server は提示された certificate を、`jwks` / `jwks_uri` を通じて Client に設定または登録された certificate と照合します。

どちらの場合も、OAuth request の `client_id` が Client configuration を特定し、TLS handshake で提示された certificate が authentication credential として使われます。

## 6. Certificate-bound Access Token とは別の機構である

RFC 8705 §1 と §4 は、mutual-TLS OAuth Client Authentication と mutual-TLS certificate-bound Access Token が別の mechanism であり、必ずしも一緒に使用する必要はないことを明記しています。

この記事では Client Authentication だけを扱います。Access Token を Client certificate に bind し、Resource Server がその binding を検証する処理は RFC 8705 §3 の別のテーマです。

## 一次資料

- RFC Editor: [RFC 8705 — OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens](https://www.rfc-editor.org/rfc/rfc8705.html)

参照した主要節: §1, §2, §2.1, §2.1.2, §2.2, §2.2.1, §2.2.2, §4  
最終確認: 2026-09-23
