---
layout: post
title: "WebAuthn の attestation conveyance：none / indirect / direct / enterprise の意味"
date: 2026-09-22 19:40:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** WebAuthn registration の `attestation` option と返却される attestation information の関係を実装・レビューする Relying Party（RP）の担当者  
**この記事で伝えること:** `PublicKeyCredentialCreationOptions.attestation` の配置、`none` / `indirect` / `direct` / `enterprise` の意味、および attestation object との関係  
**扱わないこと:** 個別 attestation statement format の検証手順、attestation trust anchor の選定、証明書 chain validation、FIDO Metadata Service、authentication ceremony

WebAuthn Level 3 では、RP は credential generation 時に `attestation` member を使って attestation conveyance に関する preference を指定できます。本記事は W3C Web Authentication Level 3 §5.4、§5.4.7、§6.5、§6.5.4、§7.1 に範囲を限定します。

**The `attestation` member expresses an RP preference about attestation conveyance during credential generation.**  
（`attestation` member は、credential generation における attestation conveyance について RP の preference を表します。）

## 1. attestation は credential creation options の member

§5.4 では `attestation` は `PublicKeyCredentialCreationOptions` の DOMString member として定義され、default は `"none"` です。RP はこの OPTIONAL member を使用できます（**MAY**, §5.4）。値は `AttestationConveyancePreference` の member とすることが **SHOULD** です。Client platform は unknown value を無視し、その member が存在しない場合と同様に扱わなければなりません（**MUST**, §5.4）。

### 非規範的な配置例

次は `attestation` の配置だけを確認するための非規範的な最小例です。`challenge`、user account、RP、algorithm の各値は illustrative value であり、この例自体に追加の規範的意味はありません。

```json
{
  "publicKey": {
    "rp": { "name": "Illustrative RP" },
    "user": {
      "id": "aWxsdXN0cmF0aXZlLXVzZXI",
      "name": "illustrative-user",
      "displayName": "Illustrative User"
    },
    "challenge": "aWxsdXN0cmF0aXZlLWNoYWxsZW5nZQ",
    "pubKeyCredParams": [
      { "type": "public-key", "alg": -7 }
    ],
    "attestation": "direct"
  }
}
```

- `attestation`: DOMString、OPTIONAL、default は `"none"`。
- 配置: `navigator.credentials.create()` に渡す `CredentialCreationOptions.publicKey`、すなわち `PublicKeyCredentialCreationOptions` の member。
- §5.4.7 で定義される値: `none`、`indirect`、`direct`、`enterprise`。

## 2. none：RP は authenticator attestation を求めない

§5.4.7 では `none` は、RP が authenticator attestation に関心を持たないことを表します。これは default です。unknown value も `none` と同じ behavior に fallback します。

Authenticator が self attestation ではない attestation statement を生成した場合、client はそれを None attestation statement に置き換えます（§5.4.7）。また credential creation の client-side algorithm では、`pkOptions.attestation` が `none` の場合、authenticator に渡す `attestationFormats` を `"none"` だけを含む list に設定します（§5.1.3）。

## 3. indirect：client が conveyance の方法を決められる

`indirect` は、RP が verifiable attestation statement を受け取りたい一方、その statement をどのように得るかを client が決定できる preference です（§5.4.7）。

Client は user privacy の保護などのために、authenticator が生成した attestation statement を Anonymization CA が生成した statement に置き換えることができます（**MAY**, §5.4.7）。ただし §5.4.7 は、`indirect` を指定しても RP が verifiable attestation statement を取得できる保証はないことを明記しています。

## 4. direct：authenticator が生成した statement を求める

`direct` は、RP が authenticator によって生成された attestation statement を受け取りたいことを表します（§5.4.7）。

`direct` は attestation statement format そのものを指定する値ではありません。§6.5 は、attestation type と attestation statement format は authenticator が選択し、RP は `attestation` と `attestationFormats` によって preference を signal できるだけであると説明しています。

**`direct` is an attestation conveyance preference, not an attestation statement format identifier.**  
（`direct` は attestation conveyance の preference であり、attestation statement format identifier ではありません。）

## 5. enterprise：controlled deployment 向けの enterprise attestation

`enterprise` は、RP が enterprise attestation を受け取りたいことを表します。§5.4.7 は enterprise attestation を、Authenticator を一意に識別し得る情報を含む可能性がある attestation statement と説明し、組織が registration を特定の Authenticator に結び付ける controlled deployment を用途として示しています。

User agent は、要求された RP ID について user agent または authenticator の configuration が許可しない限り、そのような attestation を提供してはなりません（**MUST NOT**, §5.4.7）。許可されている場合、user agent は Authenticator に enterprise attestation が要求されたことを signal し、得られた AAGUID と attestation statement を変更せず RP に convey することが **SHOULD** です（§5.4.7）。

どの RP ID に enterprise attestation を許可するかは configuration に依存します。本記事では特定の configuration policy を推奨しません。

## 6. response では attestationObject を受け取る

Registration が成功すると、RP 側の script は `AuthenticatorAttestationResponse` を受け取ります。§7.1 step 13 では、RP は `response.attestationObject` を CBOR decode して `fmt`、`authData`、`attStmt` を取得します。

§6.5.4 が定義する attestation object の構造は、概念的には次の CBOR map です。次は配置を示すための非規範的な表記です。

```text
{
  authData: <bytes>,
  fmt: <text>,
  attStmt: <map or array>
}
```

- `authData`: authenticator data の byte array。
- `fmt`: attestation statement format identifier。
- `attStmt`: `fmt` が定める attestation statement。map または array。

§7.1 steps 21–24 は `fmt` に対応する verification procedure と、その結果に基づく trustworthiness assessment を定めています。これらの個別 format、trust anchor、certificate chain の詳細は本記事の scope 外です。

<pre class="mermaid">
flowchart TD
    A[RP: attestation preference] --> B[Client]
    B --> C[Authenticator]
    C --> D[attestation object]
    D --> E[Client]
    E --> F[RP: fmt / authData / attStmt]
</pre>

この図は §5.4.7、§6.5.4、§7.1 の関係を示す非規範的な要約です。`none` / `indirect` / `direct` / `enterprise` によって conveyance の扱いが異なるため、図は特定の statement format や trust property を追加していません。

## 7. Article brief

- **Reader:** WebAuthn registration の `attestation` option と返却される attestation information の関係を実装・レビューする RP 担当者。
- **Question:** `attestation` の `none` / `indirect` / `direct` / `enterprise` は何を指定し、registration response の attestation object とどう関係するのか。
- **Answer:** `attestation` の配置と default、4つの conveyance preference の意味、`attestationObject` の `fmt` / `authData` / `attStmt` までの関係を理解できる。
- **Scope:** `PublicKeyCredentialCreationOptions.attestation`、`AttestationConveyancePreference`、attestation object の最小構造、§7.1 における decode と attestation verification への接続点。
- **Out of scope:** 個別 attestation statement format の検証手順、attestation trust anchor の選定、証明書 chain validation、FIDO Metadata Service、authentication ceremony。
- **Primary sources:** W3C Web Authentication Level 3 §5.4, §5.4.7, §6.5, §6.5.4, §7.1。
- **Diagram:** RP の conveyance preference から Client / Authenticator を経て attestation object が RP に返り、`fmt` / `authData` / `attStmt` を得るまでの縦方向 flowchart。

## 8. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §5.4, §5.4.7, §6.5, §6.5.4, §7.1  
最終確認: 2026-09-22
