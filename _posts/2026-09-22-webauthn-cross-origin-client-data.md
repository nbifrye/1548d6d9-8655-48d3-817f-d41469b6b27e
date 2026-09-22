---
layout: post
title: "WebAuthn の crossOrigin / topOrigin：cross-origin iframe を RP が検証する"
date: 2026-09-22 17:39:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** WebAuthn を iframe 内で利用する構成を実装・レビューする Relying Party（RP）の担当者  
**この記事で伝えること:** `clientDataJSON.crossOrigin` / `topOrigin` が何を表し、registration / authentication で RP が何を検証するか  
**扱わないこと:** `origin` 自体の一般的な validation、Related Origin Requests、RP ID / `rpIdHash`、challenge、UP / UV、signature、attestation、Permissions Policy の詳細

WebAuthn Level 3 の `CollectedClientData` には、cross-origin の ancestor を持つ context を表すための `crossOrigin` と `topOrigin` があります。RP の verification procedure は、これらが示す iframe context が RP の期待と一致することを検証します。本記事は W3C Web Authentication Level 3 §5.8.1、§7.1、§7.2、§13.4.9 に範囲を限定します。

## 1. crossOrigin と topOrigin は CollectedClientData の member

§5.8.1 では `crossOrigin` は OPTIONAL boolean、`topOrigin` は OPTIONAL DOMString と定義されています。

- `crossOrigin`: internal method に渡された `sameOriginWithAncestors` の逆の値を表します。
- `topOrigin`: requester の fully qualified top-level origin を表します。call が ancestors と same-origin ではない場合、すなわち `crossOrigin` が `true` の場合にだけ設定されます。

Client の registration algorithm では §5.1 step 13、authentication algorithm では §5.2 step 10 で、`crossOrigin` と `topOrigin` を `CollectedClientData` に設定します。

**`crossOrigin` indicates whether the caller is cross-origin with its ancestors; `topOrigin` identifies the top-level origin in that case.**  
（`crossOrigin` は caller が ancestor と cross-origin かを示し、その場合の top-level origin を `topOrigin` が示します。）

### 非規範的な構造例

次は cross-origin iframe から ceremony が開始された場合の配置を確認するための非規範的な例です。`challenge` の値に規範的意味はなく、`origin` / `topOrigin` も構造説明用の illustrative value です。

```json
{
  "type": "webauthn.get",
  "challenge": "illustrative-challenge",
  "origin": "https://login.example",
  "crossOrigin": true,
  "topOrigin": "https://portal.example"
}
```

- `crossOrigin`: boolean、OPTIONAL。
- `topOrigin`: DOMString、OPTIONAL。
- 配置: `AuthenticatorResponse.clientDataJSON` を UTF-8 decode し、JSON parse して得る client data の member。
- `topOrigin` は `crossOrigin` が `true` となる context で設定されます。

## 2. registration での検証

§7.1 は registration ceremony で RP が実行する verification procedure を定めています。

§7.1 step 10 では、`C.crossOrigin` が存在して `true` の場合、RP は credential が ancestors と same-origin ではない iframe 内で作成されたことを期待しているか検証します。

§7.1 step 11 では、`C.topOrigin` が存在する場合、RP は次の2点を検証します。

1. credential が ancestors と same-origin ではない iframe 内で作成されたことを RP が期待していること。
2. `C.topOrigin` が、RP が sub-frame されることを期待する page の origin と一致すること。

## 3. authentication での検証

§7.2 step 13 では、`C.crossOrigin` が存在して `true` の場合、RP は credential が ancestors と same-origin ではない iframe 内で使用されることを期待しているか検証します。

§7.2 step 14 では、`C.topOrigin` が存在する場合、RP は cross-origin iframe での利用を期待していることと、`C.topOrigin` が RP の期待する embedding page の origin に一致することを検証します。

<pre class="mermaid">
flowchart TD
    A[clientDataJSON] --> B{crossOrigin = true?}
    B -->|Yes| C[Cross-origin iframe を期待するか検証]
    B -->|No / absent| D[topOrigin を確認]
    C --> D
    D --> E{topOrigin present?}
    E -->|Yes| F[期待する top-level origin と照合]
    E -->|No| G[後続の検証へ]
    F --> G
</pre>

この図は §7.1 steps 10–11 と §7.2 steps 13–14 の関係を示す非規範的な要約です。

## 4. topOrigin が存在する場合は expected value を検証する

§13.4.9 は `topOrigin` が存在する場合、RP がその値が expected であることを検証することを **MUST** としています。検証は exact string matching または RP が必要とする他の方法で行うことができます（**MAY**）。

仕様は、cross-origin iframe を許可する domain の集合や判定方法を一律には定めていません。§13.4.9 は複数の構成例を示しており、どの origin を expected とするかは RP の構成に応じます。本記事では特定の allowlist や判定方法を推奨しません。

**When `topOrigin` is present, the RP MUST validate that its value is expected.**  
（`topOrigin` が存在する場合、RP はその値が期待する値であることを検証しなければなりません。）

## 5. origin validation とは対象が異なる

`origin` は requester の origin であり、§7.1 step 9 / §7.2 step 12 で RP の expected origin と照合されます。一方、`topOrigin` は cross-origin ancestor がある場合の top-level origin を表します。

したがって `origin` の検証と `crossOrigin` / `topOrigin` の検証は、同じ `CollectedClientData` に含まれていても対象が異なります。本記事では後者だけを中心テーマとします。

## 6. Article brief

- **Reader:** WebAuthn を iframe 内で利用する構成を実装・レビューする RP 担当者。
- **Question:** `clientDataJSON.crossOrigin` と `topOrigin` は何を表し、RP は registration / authentication で何を検証するのか。
- **Answer:** cross-origin ancestor context の表現、`topOrigin` の配置、§7.1 / §7.2 の RP verification、§13.4.9 の expected-value validation を理解できる。
- **Scope:** §5.8.1 の `crossOrigin` / `topOrigin`、§7.1 steps 10–11、§7.2 steps 13–14、§13.4.9 の `topOrigin` validation。
- **Out of scope:** `origin` 自体の一般的な validation、Related Origin Requests、RP ID / `rpIdHash`、challenge、UP / UV、signature、attestation、Permissions Policy の詳細。
- **Primary sources:** W3C Web Authentication Level 3 §5.8.1, §7.1, §7.2, §13.4.9。
- **Diagram:** decoded client data の `crossOrigin` / `topOrigin` から RP の expected iframe context と top-level origin を検証する縦方向 flowchart。

## 7. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §5.8.1, §7.1, §7.2, §13.4.9  
最終確認: 2026-09-22
