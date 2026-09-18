---
layout: post
title: "RFC 9449：DPoP proof は HTTP request の何を証明するのか"
date: 2026-09-19 00:44:00 +0900
categories: [authorization, oauth, dpop]
---

DPoP（Demonstrating Proof of Possession）は、OAuth 2.0 の token を application layer で sender-constrain するための仕組みです。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** DPoP を実装・レビューする OAuth Client / Resource Server 開発者  
**この記事で伝えること:** DPoP proof JWT が HTTP request のどの情報と鍵の所持を結び付け、protected resource access で何を追加検証するか  
**扱わないこと:** Authorization Server による access token 発行・binding の詳細、DPoP nonce、authorization code と DPoP key の binding、PAR との組み合わせ

この記事では RFC 9449 全体を要約しません。DPoP proof の構造と検証、および DPoP-bound access token を protected resource へ提示するときの処理に範囲を限定します。

## 1. DPoP proof と HTTP request

RFC 9449 §4 は、DPoP proof を Client が作成する JWT として定義しています。Client は request ごとに DPoP proof を作成し、`DPoP` HTTP header field に設定します。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant RS as Resource Server
    C->>C: request 用 DPoP proof を生成
    C->>RS: Access Token + DPoP proof
    RS->>RS: proof の署名と claims を検証
    RS->>RS: token と公開鍵の binding を検証
    RS-->>C: Protected Resource Response
</pre>

DPoP proof が示すのは、proof に含まれる公開鍵に対応する秘密鍵を Client が所持していることです。RFC 9449 §4 は、DPoP proof 単体を authentication または access control mechanism として扱っていません。

## 2. JOSE Header が示す鍵と署名方式

RFC 9449 §4.2 では、DPoP proof JWT の JOSE Header に少なくとも次の parameter を含めることを要求しています。

- **`typ`:** 値は `dpop+jwt`。
- **`alg`:** asymmetric digital signature algorithm。`none` または symmetric algorithm を使用してはならない（MUST NOT）。
- **`jwk`:** Client が選択した公開鍵。private key を含めてはならない（MUST NOT）。

受信側 Server は §4.3 に従い、`jwk` に含まれる公開鍵で JWT signature を検証します。この検証により、request の送信者が proof を署名した秘密鍵を所持していることを確認します。

## 3. `htm` と `htu` が request に結び付ける情報

DPoP proof の payload には `jti`、`htm`、`htu`、`iat` が必要です。

- **`jti`:** proof の unique identifier。
- **`htm`:** proof を付与する HTTP request の method。
- **`htu`:** proof を付与する HTTP request の target URI。query と fragment は含めません。
- **`iat`:** proof JWT の creation timestamp。

Server は §4.3 で、`htm` が現在の request method と一致すること、および `htu` が受信した request の HTTP URI と一致することを確認しなければなりません（MUST）。`htu` の比較では query と fragment を無視します。

<pre class="mermaid">
flowchart TD
    A[DPoP proof を受信] --> B[JWT signature を検証]
    B --> C[htm と HTTP method を照合]
    C --> D[htu と request URI を照合]
    D --> E[iat または nonce による時刻を確認]
    E --> F[proof の検証を継続]
</pre>

RFC 9449 §4.2 は、HTTP request のうち proof に含める情報を method と URI に限定しています。したがって、DPoP proof は一般的な HTTP header や message body の integrity を直接提供するものではありません。この点は §11.7 でも明記されています。

## 4. protected resource access では `ath` が追加される

DPoP proof を DPoP-bound access token とともに protected resource へ提示する場合、RFC 9449 §4.2 と §7 は `ath` claim を要求しています。

`ath` は、関連する access token の値を ASCII encoding し、その SHA-256 hash を base64url encoding した値です。

Resource Server は、提示された access token から同じ hash を計算し、proof の `ath` と一致することを確認します。これにより、DPoP proof と特定の access token value が結び付きます。

`ath` だけでは proof の replay 防止や request への binding は完結しません。§7 は、proof の time window と `htm`、`htu` なども検証する必要があると説明しています。

## 5. access token と DPoP key の binding

RFC 9449 §6 は、Resource Server が access token が DPoP-bound かどうかを識別し、その token が binding されている公開鍵を確認できなければならない（MUST）と規定しています。

§7.1 では、Resource Server は DPoP-bound access token を受け取った場合、少なくとも次を確認します。

1. HTTP request に `DPoP` header field の proof が存在する。
2. proof を §4.3 の規則に従って検証する。
3. proof の公開鍵が access token に binding された公開鍵と一致する。
4. protected resource access に必要な `ath` を検証する。
5. access token 自体についても必要な検証を行う。

これらの検証がすべて成功しない限り、Resource Server は resource への access を許可してはなりません（MUST NOT）。

## 6. `Authorization` と `DPoP` は別の header field

DPoP-bound access token は、RFC 9449 §7.1 で定義される `DPoP` authentication scheme を使って `Authorization` header field に設定します。一方、proof JWT は `DPoP` header field に設定します。

概念上の request は次の構成になります。

```http
Authorization: DPoP <access-token>
DPoP: <proof-jwt>
```

ここで `<access-token>` と `<proof-jwt>` は異なる値です。Resource Server は token の有効性だけでなく、proof と token の key binding も検証します。

## 7. DPoP proof が直接カバーしないもの

RFC 9449 §11.7 は、DPoP が request payload や一般的な request header の integrity を保証しないことを説明しています。proof に含まれる HTTP request 情報は `htu` と `htm` です。

また、§4 は DPoP proof 自体が authentication や access control の仕組みではないとしています。Protected resource access では、access token の検証と DPoP binding の検証を組み合わせて処理します。

## 8. 一次資料

- RFC Editor: [RFC 9449 — OAuth 2.0 Demonstrating Proof of Possession (DPoP)](https://www.rfc-editor.org/rfc/rfc9449.html)

参照した主要節: §4, §4.2, §4.3, §6, §7, §7.1, §11.7  
最終確認: 2026-09-19
