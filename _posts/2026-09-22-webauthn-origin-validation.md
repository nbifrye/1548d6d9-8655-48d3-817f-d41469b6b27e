---
layout: post
title: "WebAuthn の origin validation：clientDataJSON.origin を RP が検証する要件"
date: 2026-09-22 13:41:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Security Practice / Requirement  
**対象読者:** WebAuthn の registration / authentication response をサーバー側で検証する Relying Party（RP）の実装・レビュー担当者  
**この記事で伝えること:** `clientDataJSON` の `origin` がどこに入り、registration / authentication で RP が何を検証し、許容 origin の判断について仕様が何を定めているか  
**扱わないこと:** Related Origin Requests、cross-origin iframe の `crossOrigin` / `topOrigin`、RP ID の決定、`rpIdHash`、challenge、signature、attestation の検証

WebAuthn Level 3 では、Client が収集した origin は `clientDataJSON` に含まれます。RP は registration と authentication の双方で、その `origin` が RP の期待する origin であることを検証します。本記事は W3C Recommendation §5.8.1、§7.1、§7.2、§13.4.9 に範囲を限定します。

## 1. origin は clientDataJSON に入る

§5.8.1 の `CollectedClientData` は、WebAuthn ceremony で Client が収集し、`clientDataJSON` としてシリアライズするデータを定義しています。その member の一つが `origin` です。

`origin` は、ceremony の caller origin を表す文字列です。RP が response を受け取ると、`response.clientDataJSON` を UTF-8 decode し、JSON として解釈して `origin` を参照します。

### 非規範的な最小構造例

次は `origin` の配置を確認するための非規範的な例です。値は illustrative です。

```json
{
  "type": "webauthn.get",
  "challenge": "illustrative-base64url-challenge",
  "origin": "https://login.example.org"
}
```

この JSON は authentication ceremony の例です。`origin` は HTTP header や WebAuthn request option の member ではなく、Client が返す `clientDataJSON` 内の member です。

- `type`: DOMString。authentication では `webauthn.get`。
- `challenge`: DOMString。RP が渡した challenge の base64url encoding。
- `origin`: DOMString。Client が収集した caller origin。

本記事では `origin` の検証だけを扱います。`type` と `challenge` にも独立した verification step がありますが、その詳細は scope 外です。

## 2. registration では expected origin を検証する

§7.1 の registration verification では、RP は `clientDataJSON` を decode / parse した後、`C.origin` が RP の期待する origin であることを検証します（§7.1 step 9）。

処理の位置関係は次のとおりです。

<pre class="mermaid">
flowchart TD
    A[Registration response] --> B[clientDataJSON を decode]
    B --> C[JSON を parse]
    C --> D[C.origin を取得]
    D --> E{RP が期待する origin か}
    E -->|Yes| F[後続の verification]
    E -->|No| G[registration を失敗]
</pre>

§7.1 は、すべての verification step が成功した場合に credential record を保存して ceremony を継続し、それ以外では registration ceremony を fail する手順を定義しています。

## 3. authentication でも同じ origin validation がある

§7.2 の authentication assertion verification でも、RP は `clientDataJSON` を decode / parse し、`C.origin` が RP の期待する origin であることを検証します（§7.2 step 12）。

<pre class="mermaid">
flowchart TD
    A[Authentication response] --> B[clientDataJSON を decode]
    B --> C[JSON を parse]
    C --> D[C.origin を取得]
    D --> E{RP が期待する origin か}
    E -->|Yes| F[後続の verification]
    E -->|No| G[authentication を失敗]
</pre>

registration と authentication のどちらでも、response に入っていた origin をそのまま信頼するのではなく、RP が期待する origin と照合する verification step が存在します。

**The RP verifies the origin carried in client data against an origin it expects.**  
（RP は client data に含まれる origin を、自身が期待する origin と照合して検証します。）

## 4. unexpected origin は受け入れてはならない

§13.4.9 は RP による origin validation の security consideration を定めています。

RP は unexpected な `origin` を受け入れてはなりません（**MUST NOT**, §13.4.9）。仕様は、WebAuthn credential の scope が RP ID 外での利用を防ぐ一方、RP による origin validation は、Authenticator が credential scope を正しく enforce しない場合に対する追加の保護層になると説明しています。

一方、validation method 自体については exact string matching または RP が必要とする別の方法を使用してもよい（**MAY**, §13.4.9）とされています。

単一 origin `https://example.org` だけで提供される web application について、仕様は `origin` が `https://example.org` と正確に一致することを要求すべきとしています（**SHOULD**, §13.4.9）。

## 5. subdomain を許容する場合の規範要件

§13.4.9 は subdomain origin についても要件を示しています。

RP は default では assertion verification 時に subdomain `origin` を許可すべきではありません（**SHOULD NOT**, §13.4.9）。RP が subdomain `origin` を許可する必要がある場合、public key credential の scope 内で許可した subdomain に untrusted code を提供してはなりません（**MUST NOT**, §13.4.9）。

ここで仕様は、すべての deployment に単一の origin allowlist 構成を要求しているわけではありません。どの origin を RP が期待するかは deployment に依存します。本記事では特定の allowlist 設計を推奨しません。

**The specification requires rejection of unexpected origins, while the set of expected origins is deployment-specific.**  
（仕様は unexpected origin の拒否を要求しますが、expected origin の集合は deployment 固有です。）

## 6. origin と RP ID は同じ検証項目ではない

`clientDataJSON.origin` の validation と authenticator data の `rpIdHash` validation は別の verification step です。

- registration: `origin` は §7.1 step 9、`rpIdHash` は §7.1 step 14。
- authentication: `origin` は §7.2 step 12、`rpIdHash` は §7.2 step 15。

したがって、`rpIdHash` の検証を行うことは `origin` verification step の代替ではありません。本記事では RP ID の決定規則や `rpIdHash` の計算方法までは扱いません。

## 7. Article brief

- **Reader:** WebAuthn registration / authentication response の server-side verification を実装・レビューする RP 担当者。
- **Question:** `clientDataJSON.origin` はどこにあり、RP は registration / authentication で何を照合し、unexpected origin をどう扱う必要があるか。
- **Answer:** `origin` の配置、§7.1 / §7.2 の expected-origin verification、§13.4.9 の MUST NOT / MAY / SHOULD / SHOULD NOT と deployment-specific な境界を区別して理解できる。
- **Scope:** `CollectedClientData.origin`、registration / authentication の RP origin verification、§13.4.9 の origin validation requirements。
- **Out of scope:** Related Origin Requests、`crossOrigin` / `topOrigin`、RP ID determination、`rpIdHash` の詳細、challenge、signature、attestation。
- **Primary sources:** W3C Web Authentication Level 3 §5.8.1, §7.1, §7.2, §13.4.9。
- **Diagram:** registration / authentication response から `clientDataJSON.origin` を取り出し expected origin と照合する縦方向 flowchart。

## 8. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §5.8.1, §7.1, §7.2, §13.4.9  
最終確認: 2026-09-22
