---
layout: post
title: "WebAuthn の UP flag：user presence と RP の検証"
date: 2026-09-22 18:39:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** WebAuthn の registration / authentication response を検証する Relying Party（RP）の実装・レビュー担当者  
**この記事で伝えること:** authenticator data の UP flag が何を表し、Authenticator がいつ set し、RP が registration / authentication でいつ検証するか  
**扱わないこと:** user verification（UV）の要求と検証、challenge、origin、RP ID、signature、attestation、credential backup state、signature counter

WebAuthn Level 3 では、Authenticator が test of user presence を実行したかどうかを authenticator data の `UP` flag で表します。本記事は W3C Recommendation §4、§6.1、§6.3.2、§6.3.3、§7.1、§7.2 に範囲を限定します。

## 1. user presence は user verification とは異なる

§4 は test of user presence を、ユーザーが Authenticator に対して通常は触れるなどの操作を行い、Boolean result を得る単純な authorization gesture と定義しています。この test は biometric recognition や password / PIN のような shared secret の提示を含む user verification ではありません。

**User presence shows that a user interacted with the authenticator; it does not identify or verify that user.**  
（user presence はユーザーが Authenticator と操作したことを示しますが、そのユーザーの識別や本人確認を行うものではありません。）

UP と UV は authenticator data でも別の bit です。両方の処理が行われた場合は、両方の flag が set されます（§6.1）。

## 2. UP flag は authenticator data の flags byte に入る

`UP` は JSON member ではありません。§6.1 の authenticator data にある `flags` byte の bit 0 です。

- `UP`: flags の bit 0。
- `UP=1`: Authenticator が test of user presence を実行した。
- `UP=0`: test of user presence を実行したことを示していない。

Authenticator は test of user presence を実行した場合に、かつその場合に限って `UP` flag を set します（**SHALL**, §6.1）。

### 非規範的な構造例

次は配置だけを確認するための非規範的な例です。値は illustrative です。

```text
authenticator data
  bytes 0..31 : rpIdHash
  byte 32     : flags
  bytes 33..36: signCount

flags = 0x01
        00000001
               ^
               +-- bit 0 UP = 1
```

`flags` byte には UP 以外の flag も定義されているため、この例の `0x01` を一般的な WebAuthn response の固定値として扱うことはできません。

## 3. Authenticator が user presence を要求された場合

`authenticatorMakeCredential` operation では、`requireUserPresence` が `true` の場合、authorization gesture は test of user presence を含まなければなりません（**MUST**, §6.3.2）。

`authenticatorGetAssertion` operation でも、`requireUserPresence` が `true` の場合、authorization gesture は test of user presence を含まなければなりません（**MUST**, §6.3.3）。

この test が実行された結果は、§6.1 の規則により `UP` flag に反映されます。

<pre class="mermaid">
flowchart TD
    A[Authenticator operation] --> B{user presence test を実行}
    B -->|Yes| C[UP = 1]
    B -->|No| D[UP = 0]
    C --> E[authenticator data]
    D --> E
</pre>

## 4. registration では conditional mediation が分岐になる

RP の registration verification は §7.1 に定義されています。

§7.1 step 15 では、`options.mediation` が `conditional` に設定されていない場合、RP は `authData.flags` の UP bit が set されていることを検証します。

したがって、この step はすべての registration ceremony に無条件で UP verification を課しているわけではありません。`mediation=conditional` の場合は、この step の条件に該当しません。

本記事では conditional mediation 自体の credential discovery や UI behavior は扱いません。

## 5. authentication では RP が UP=1 を検証する

Authentication assertion の verification では、§7.2 step 16 が RP に `authData.flags` の UP bit が set されていることの検証を要求します。

処理関係を UP に限定すると次のようになります。

<pre class="mermaid">
flowchart TD
    A[Assertion response] --> B[authenticatorData を読む]
    B --> C[flags の UP bit を読む]
    C --> D{UP = 1}
    D -->|Yes| E[次の verification step へ]
    D -->|No| F[verification を満たさない]
</pre>

§7.2 は authentication ceremony を行う RP に一連の verification procedure を **MUST** として課しており、その中の step 16 が UP bit の検証です。

## 6. UP と UV を同じ意味にしない

§6.1 は UP と UV を別々に定義しています。

- UP は test of user presence を実行した場合に、かつその場合に限って set されます（**SHALL**, §6.1）。
- UV は user verification を実行した場合に、かつその場合に限って set されます（**SHALL**, §6.1）。

Authenticator が両方を実行した場合、両 flag が set されます。したがって `UP=1` だけから `UV=1` を導くことはできません。

**UP and UV record different authenticator actions and are verified under different RP rules.**  
（UP と UV は異なる Authenticator の処理を記録し、RP 側でも異なる規則で検証されます。）

UV の要求を決める `userVerification` option と §7.1 / §7.2 の UV verification は別記事のテーマとし、ここでは扱いません。

## 7. Article brief

- **Reader:** WebAuthn registration / authentication response verification を実装・レビューする RP 担当者。
- **Question:** UP flag は何を意味し、Authenticator はいつ set し、RP はどの ceremony でどう検証するのか。
- **Answer:** UP は test of user presence の実行結果を表す flags bit であり、§6.1 の生成規則と §7.1 / §7.2 の RP verification の違いを理解できる。
- **Scope:** test of user presence、authenticator data の UP flag、Authenticator operation と RP verification。
- **Out of scope:** user verification / UV、conditional mediation の詳細、challenge、origin、RP ID、signature、attestation、BE / BS、signCount。
- **Primary sources:** W3C Web Authentication Level 3 §4, §6.1, §6.3.2, §6.3.3, §7.1, §7.2。
- **Diagram:** UP flag の生成関係と authentication 時の UP verification を示す縦方向 flowchart。

## 8. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §4, §6.1, §6.3.2, §6.3.3, §7.1, §7.2  
最終確認: 2026-09-22
