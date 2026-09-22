---
layout: post
title: "RFC 9449：DPoP proof は HTTP request の何を証明するのか"
date: 2026-09-19 00:44:00 +0900
categories: [authorization, oauth, dpop]
---

DPoP（Demonstrating Proof of Possession）は、OAuth 2.0 の access token / refresh token をアプリケーション層で sender-constrained（送信者制約付き）にするための仕組みです。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** DPoP を実装・レビューする OAuth Client / Resource Server 開発者  
**この記事で伝えること:** DPoP proof JWT が HTTP request のどの情報と鍵の所持を結び付け、protected resource（保護リソース）へのアクセス時に Resource Server が何を追加検証するか  
**扱わないこと:** Authorization Server による access token 発行・binding の詳細、DPoP nonce、authorization code と DPoP key の binding、PAR との組み合わせ

この記事では RFC 9449 全体を要約しません。DPoP proof の構造と検証、および DPoP-bound access token を保護リソースへ提示するときの処理に範囲を限定します。

## 1. DPoP proof と HTTP request

RFC 9449 §4 は、DPoP proof を Client が作成し、HTTP request の `DPoP` header field で送信する JWT として定義しています。HTTP request ごとに一意な DPoP proof が必要です。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant RS as Resource Server
    C->>C: HTTP request 用の DPoP proof を生成
    C->>RS: Access Token + DPoP proof
    RS->>RS: proof の署名と claims を検証
    RS->>RS: token と公開鍵の binding を検証
    RS-->>C: Protected Resource Response
</pre>

有効な DPoP proof は、proof JWT の署名に使われた秘密鍵を Client が所持していることを Server に示します。DPoP proof 自体は authentication や access control の仕組みではなく、proof だけでアクセス可否を決定することはできません。

## 2. JOSE Header が示す鍵と署名方式

RFC 9449 §4.2 では、DPoP proof JWT の JOSE Header に少なくとも次の parameter を含めることを要求しています。

- **`typ`:** 値は `dpop+jwt`。
- **`alg`:** JWS の asymmetric digital signature algorithm。値を `none` または symmetric algorithm にしてはならない（MUST NOT）。
- **`jwk`:** Client が選択した公開鍵を表す JWK。private key を含めてはならない（MUST NOT）。

受信側 Server は §4.3 に従い、`DPoP` HTTP request header field が複数存在しないこと、header field value が単一の well-formed JWT であること、§4.2 の必須 claim がすべて含まれること、`typ` が `dpop+jwt` であることを確認しなければなりません（MUST）。さらに、`alg` が登録済みの asymmetric digital signature algorithm であり、アプリケーションでサポートされ、local policy 上許容されていることを確認し、`jwk` に含まれる公開鍵で JWT signature を検証しなければなりません（MUST）。§11.6 はこれに加えて、DPoP proof の署名には安全とみなされる asymmetric digital signature algorithm だけを使用できるよう実装者が保証しなければならない（MUST）としています。

この署名検証によって、Server は DPoP proof に含まれる公開鍵に対応する秘密鍵を送信者が所持していることを確認します。

## 3. `htm` と `htu` が HTTP request に結び付ける情報

DPoP proof の payload は、少なくとも `jti`、`htm`、`htu`、`iat` を含まなければなりません（MUST）。

- **`jti`:** DPoP proof JWT の識別子。同じ context と有効期間内で同じ値が再利用される確率が無視できるほど小さくなるよう割り当てなければなりません（MUST）。
- **`htm`:** proof を付与する HTTP request の method。
- **`htu`:** proof を付与する HTTP request の target URI。query と fragment は含めません。
- **`iat`:** proof JWT の creation timestamp。

Server は §4.3 に従い、`htm` が現在の HTTP request method と一致すること、および `htu` が DPoP proof を受信した HTTP request の URI と一致することを確認しなければなりません（MUST）。`htu` の比較では query と fragment を無視します。

さらに RFC 9449 §4.3 は、`htu` の比較前に RFC 3986 の syntax-based normalization と scheme-based normalization を行うことを Server に推奨しています（SHOULD）。したがって、`htu` の検証を単純な文字列一致だけとして実装するのは、RFC 9449 の比較手順を十分に表していません。

また、§4.3 は `iat` または Server が `nonce` により管理する timestamp から求めた creation time が許容可能な time window 内であることの確認を要求しています。§11.1 は replay を制限するため、Server が DPoP proof を作成後の限られた期間だけ受理しなければならない（MUST）とし、秒から分程度の比較的短い期間を推奨しています。

<pre class="mermaid">
flowchart TD
    A[DPoP proof を受信] --> B[JWT の形式と署名を検証]
    B --> C[htm と HTTP method を照合]
    C --> D[htu と request URI を照合]
    D --> E[iat または nonce で時刻を確認]
    E --> F[proof の検証を継続]
</pre>

RFC 9449 §4.2 が基本要件として HTTP request から DPoP proof に含めるのは HTTP method と URI です。一般的な request header や message body は DPoP proof の対象に含まれません。拡張や profile により追加の claim を含めることは可能ですが、RFC 9449 の基本仕様は request 全体の integrity を提供しません。

## 4. 保護リソースへのアクセスでは `ath` が追加される

DPoP proof を access token とともに保護リソースへのアクセスに使用する場合、RFC 9449 §4.2 と §7 は `ath` claim を要求しています（MUST）。

`ath` は、関連する access token の値を ASCII encoding し、その SHA-256 hash を計算した後、base64url encoding した値です。

Resource Server は、提示された access token から同じ hash を計算し、proof の `ath` と一致することを確認しなければなりません。これにより、DPoP proof と特定の access token value が結び付きます。

ただし、`ath` だけでは DPoP proof の replay 防止や HTTP request への binding は完結しません。RFC 9449 §7 は、proof の time window と `htm`、`htu` なども検証する必要があると説明しています。

## 5. access token と DPoP key の binding

RFC 9449 §6 は、Resource Server が、access token が DPoP-bound かどうかを確実に識別し、その token と DPoP proof の公開鍵との binding を検証するために十分な情報を取得できなければならない（MUST）と規定しています。

たとえば、JWT 形式の access token では `cnf.jkt` に JWK SHA-256 Thumbprint を含める方法が §6.1 で定義されています。token introspection を使用する場合は、§6.2 に従って introspection response の `cnf.jkt` から binding 情報を取得できます。

Resource Server が DPoP-bound access token を受け取った場合、主に次を検証します。

1. HTTP request に `DPoP` header field の proof が存在する。
2. proof を §4.3 の規則に従って検証する。
3. protected resource access に必要な `ath` が、提示された access token の hash と一致する。
4. proof の公開鍵が access token に binding された公開鍵と一致する。
5. access token 自体について必要な検証を行う。

§4.3 の各検証は任意の順序で実施できます。Resource Server は、必要な検証がすべて成功しない限り resource への access を許可してはなりません（MUST NOT）。

## 6. `Authorization` と `DPoP` は別の header field

DPoP-bound access token は、RFC 9449 §7.1 で定義される `DPoP` authentication scheme を使って `Authorization` request header field に設定します。一方、DPoP proof JWT は `DPoP` header field に設定します。

概念上の request は次の構成です。

```http
Authorization: DPoP <access-token>
DPoP: <proof-jwt>
```

`<access-token>` と `<proof-jwt>` は異なる値です。Resource Server は token の有効性だけでなく、proof と token の key binding も検証します。

また、`DPoP` と `Bearer` の両方をサポートする protected resource は、DPoP-bound access token が `Bearer` scheme で提示された場合、その token を拒否しなければなりません（MUST）。RFC 9449 §7.2 は、DPoP の binding を回避する downgrade を防ぐためにこの要件を規定しています。

## 7. DPoP proof が直接カバーしないもの

RFC 9449 §11.7 は、DPoP が request payload や一般的な request header の integrity を保証しないことを明記しています。DPoP proof が基本仕様で直接カバーする HTTP request 情報は `htu` と `htm` です。

そのため、DPoP proof の署名が正しくても、HTTP message 全体が署名対象になっているわけではありません。RFC 9449 §2 は、DPoP を secure transport の代替として扱ってはならず、常に HTTPS と組み合わせて使用しなければならない（MUST）と規定しています。

また、§4 は DPoP proof 自体が authentication や access control の仕組みではないとしています。保護リソースへのアクセスでは、access token の検証と DPoP binding の検証を組み合わせて処理します。

## 8. 一次資料

- RFC Editor: [RFC 9449 — OAuth 2.0 Demonstrating Proof of Possession (DPoP)](https://www.rfc-editor.org/rfc/rfc9449.html)
- RFC Editor: [RFC 9449 status / errata](https://www.rfc-editor.org/info/rfc9449/)

文書ステータス: Proposed Standard（Standards Track）  
発行: 2023-09  
参照した主要節: §2, §4, §4.2, §4.3, §6, §6.1, §6.2, §7, §7.1, §7.2, §11.1, §11.6, §11.7  
Verified Errata: EID 7646（Editorial。§4.2 の “authentication server” を “authorization server” に訂正）  
最終確認: 2026-09-22
