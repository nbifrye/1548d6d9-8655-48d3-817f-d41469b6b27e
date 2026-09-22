---
layout: post
title: "WebAuthn Level 3：userVerification と UV flag はどう対応するのか"
date: 2026-09-22 11:39:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** WebAuthn authentication の user verification を実装・レビューする Relying Party 実装者  
**この記事で伝えること:** `PublicKeyCredentialRequestOptions.userVerification` の3値と、authentication assertion の UV flag を RP がいつ検証するか  
**扱わないこと:** challenge、origin、RP ID、signature、UP flag、attestation、registration、認証器固有の PIN・biometric 実装

## Article brief

- **Reader:** WebAuthn authentication の user verification requirement と assertion verification を実装・レビューする RP 実装者
- **Question:** `userVerification` の3値は何を意味し、UV flag を RP はどの条件で確認するのか
- **Answer:** request の requirement、Authenticator の user verification、UV flag、RP verification の対応を説明する
- **Scope:** WebAuthn Level 3 §5.5、§5.8.6、§6.1、§6.3.3、§7.2
- **Out of scope:** registration、UP flag、challenge / origin / rpIdHash / signature、attestation、`uvInitialized`
- **Primary sources:** W3C Web Authentication Level 3 §5.5、§5.8.6、§6.1、§6.3.3、§7.2
- **Diagram:** RP の requirement から UV flag verification までの sequence diagram

## 1. `userVerification` は authentication request の option

`PublicKeyCredentialRequestOptions.userVerification` は `navigator.credentials.get()` に対する RP の user verification requirement を表す OPTIONAL member です（§5.5）。値は `required`、`preferred`、`discouraged` です（§5.8.6）。

以下は配置を示す非規範的な最小例です。`challenge` は request options の必須 member のため含めていますが、その生成・検証は扱いません。

```javascript
// 非規範的な例
const requestOptions = {
  publicKey: {
    challenge: authenticationChallenge,
    userVerification: "required"
  }
};
await navigator.credentials.get(requestOptions);
```

- `userVerification`: `DOMString`、OPTIONAL（§5.5）。
- 値: `required` / `preferred` / `discouraged`（§5.8.6）。

Client platform は unknown value を無視し、その member が存在しないものとして扱わなければなりません（**MUST**, §5.5）。

## 2. 3つの値の意味

### `required`

RP は user verification を要求します。response の UV flag が set されていなければ ceremony 全体を失敗させます。Client は user verification を実行できない場合、error を返さなければなりません（**MUST**, §5.8.6）。

### `preferred`

RP は可能であれば user verification を希望しますが、UV flag が set されていなくても operation を失敗させません（§5.8.6）。

### `discouraged`

RP は operation 中に user verification が使用されることを望まないことを表します（§5.8.6）。

これらは PIN、password、biometric recognition など具体的な verification modality を指定する値ではありません。

## 3. 実行結果は UV flag に現れる

Authenticator data の flags には UV flag があります。Authenticator が user verification を実行した場合に、かつその場合に限って UV flag を set することが **SHALL** です（§6.1）。

`userVerification` は RP の request option、UV flag は Authenticator が生成する authenticator data 内の flag であり、別の値です。effective user verification requirement が true の場合、authorization gesture に user verification を含めなければなりません（**MUST**, §6.3.3）。

<pre class="mermaid">
sequenceDiagram
    participant RP as Relying Party
    participant C as Client
    participant A as Authenticator
    RP->>C: userVerification requirement
    C->>A: effective UV requirement
    A->>A: user verification
    A-->>C: authenticator data (UV)
    C-->>RP: assertion response
    RP->>RP: UV flag を検証
</pre>

## 4. RP は required の場合に UV flag を検証する

§7.2 step 17 では、user verification は `pkOptions.userVerification` が `required` の場合に、かつその場合に限って required とすることが **SHOULD** です。

user verification が required と判断された場合、RP は `authData` の UV bit が set されていることを検証します。required ではないと判断した場合、RP は UV flag の値を無視します（§7.2 step 17）。

`userVerification: "required"` を送るだけで verification が完了するわけではありません。RP は返却された authenticator data の UV flag を確認します。

**`userVerification` expresses the RP's requirement; the UV flag records whether the authenticator performed user verification.**  
（`userVerification` は RP の要求を表し、UV flag は Authenticator が user verification を実行したかを記録します。）

## まとめ

`userVerification` は authentication operation に対する RP の requirement です。`required` は user verification を要求し、`preferred` は可能なら希望し、`discouraged` は使用を望まないことを表します（§5.8.6）。

Authenticator が user verification を実行した場合に、かつその場合に限って UV flag を set します（**SHALL**, §6.1）。RP が user verification を required と判断した場合は UV flag が set されていることを検証します（§7.2 step 17）。

## 一次資料

- W3C, *Web Authentication: An API for accessing Public Key Credentials Level 3*, §5.5, §5.8.6, §6.1, §6.3.3, §7.2: https://www.w3.org/TR/webauthn-3/
