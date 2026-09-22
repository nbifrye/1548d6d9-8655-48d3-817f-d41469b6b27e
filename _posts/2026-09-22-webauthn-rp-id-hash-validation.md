---
layout: post
title: "WebAuthn の rpIdHash：RP ID との binding を検証する"
date: 2026-09-22 15:45:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** WebAuthn の registration / authentication response をサーバー側で検証する Relying Party（RP）の実装・レビュー担当者  
**この記事で伝えること:** `rpIdHash` が authenticator data のどこにあり、RP が expected RP ID の SHA-256 hash と照合する要件  
**扱わないこと:** RP ID の決定手順、Related Origin Requests、origin validation、FIDO AppID extension、challenge、UP / UV、BE / BS、signature、attestation trust

WebAuthn credential は RP ID に scope されます。Authenticator data の先頭には、その RP ID を SHA-256 で hash した `rpIdHash` が入ります。RP は registration と authentication の検証時に、この値を expected RP ID から計算した hash と照合します。本記事は W3C Web Authentication Level 3 §6.1、§7.1、§7.2 に範囲を限定します。

## 1. rpIdHash は authenticator data の先頭 32 bytes

§6.1 は authenticator data を 37 bytes 以上の byte array として定義しています。先頭 32 bytes が `rpIdHash` で、その後に 1 byte の `flags` と 4 bytes の `signCount` が続きます。

`rpIdHash` は、credential が scope される RP ID の SHA-256 hash です。Authenticator は authenticator data を生成するとき、RP ID を SHA-256 で hash して `rpIdHash` を生成します（§6.1）。

### 非規範的な構造例

次は field の配置を確認するための非規範的な例です。値は illustrative です。

```text
byte 0..31   rpIdHash   = SHA-256("login.example")
byte 32      flags      = <flags byte>
byte 33..36  signCount  = <4-byte counter>
byte 37..    ...        = <optional trailing data>
```

`rpIdHash` は JSON member や HTTP header ではありません。Registration では `attestationObject` から得る authenticator data に、authentication では `AuthenticatorAssertionResponse.authenticatorData` に含まれる binary field です。

- `rpIdHash`: 32 bytes。
- 内容: credential が scope される RP ID の SHA-256 hash。
- 配置: authenticator data の byte 0..31。

## 2. registration では expected RP ID の hash と照合する

Registration verification では、RP は `attestationObject` を CBOR decode して `authData` を取得します（§7.1 step 13）。

続く §7.1 step 14 で、RP は `authData` の `rpIdHash` が、RP が期待する RP ID の SHA-256 hash であることを検証します。

<pre class="mermaid">
flowchart TD
    A[Registration response] --> B[authData を取得]
    B --> C[rpIdHash を取得]
    D[Expected RP ID] --> E[SHA-256]
    E --> F[Expected hash]
    C --> G{一致する?}
    F --> G
    G -->|Yes| H[後続の検証へ]
    G -->|No| I[検証失敗]
</pre>

**The RP verifies rpIdHash against the SHA-256 hash of its expected RP ID.**  
（RP は `rpIdHash` を、自身が期待する RP ID の SHA-256 hash と照合して検証します。）

本記事では expected RP ID をどのように決定するかは扱いません。

## 3. authentication でも同じ binding を検証する

Authentication assertion の検証でも、RP は response の `authenticatorData` を `authData` として扱います（§7.2 step 7）。

§7.2 step 15 では、`authData.rpIdHash` が expected RP ID の SHA-256 hash であることを検証します。

```text
expectedRpId = "login.example"       # illustrative
expectedHash = SHA-256(expectedRpId)

verify authData.rpIdHash == expectedHash
```

この例は非規範的です。`login.example` に規範的な意味はありません。

FIDO AppID extension を使用する authentication では §7.2 step 15 に特別な処理があります。本記事は AppID extension を scope 外とし、通常の RP ID に対する `rpIdHash` verification のみを扱います。

## 4. origin validation とは別の検証である

Registration では §7.1 step 9、authentication では §7.2 step 12 で `clientDataJSON.origin` を検証します。一方、`rpIdHash` の検証対象は authenticator data です。

したがって、origin validation と `rpIdHash` validation は同じ field の検証ではありません。本記事では origin の expected-value rules や Related Origin Requests は扱いません。

## 5. Article brief

- **Reader:** WebAuthn registration / authentication response の server-side verification を実装・レビューする RP 担当者。
- **Question:** `rpIdHash` は response のどこにあり、RP は何と照合するのか。
- **Answer:** authenticator data 先頭 32 bytes の `rpIdHash` の意味と、registration / authentication で expected RP ID の SHA-256 hash と照合する処理を理解できる。
- **Scope:** §6.1 の `rpIdHash` field と生成、§7.1 step 14、§7.2 step 15 の RP verification。
- **Out of scope:** RP ID determination、Related Origin Requests、origin validation、FIDO AppID extension、challenge、UP / UV、BE / BS、signature、attestation trust。
- **Primary sources:** W3C Web Authentication Level 3 §6.1, §7.1, §7.2。
- **Diagram:** authenticator data の `rpIdHash` と expected RP ID の SHA-256 hash を比較する縦方向 flowchart。

## 6. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §6.1, §7.1, §7.2  
最終確認: 2026-09-22
