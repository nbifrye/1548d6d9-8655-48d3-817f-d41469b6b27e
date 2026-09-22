---
layout: post
title: "WebAuthn Level 3：challenge はどこで生成し、どう検証するのか"
date: 2026-09-22 10:40:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Security Practice  
**対象読者:** WebAuthn の registration / authentication を実装・レビューする Relying Party 実装者  
**この記事で伝えること:** WebAuthn の `challenge` を RP がどこで生成し、Client に渡した値と返却された `clientDataJSON.challenge` をどのように対応付けて検証するか  
**扱わないこと:** `origin` / `rpId` / signature / attestation の検証、credential storage、user verification、認証 UI、CTAP の内部処理

この記事は WebAuthn Level 3 の cryptographic challenge に範囲を限定します。

## Article brief

- **Reader:** WebAuthn ceremony の challenge 管理と検証を実装・レビューする RP 実装者
- **Question:** registration / authentication で `challenge` は誰が生成し、どこに配置され、返却値を何と比較する必要があるのか
- **Answer:** RP が信頼する環境でランダムな challenge を生成し、creation/request options の `challenge` として Client に渡し、返却された `clientDataJSON.challenge` がその challenge の base64url encoding と一致することを検証する流れを説明する
- **Scope:** WebAuthn Level 3 §5.4.1、§5.4.2、§5.8.1、§7.1、§7.2、§13.4.3 に定義された challenge の生成・配置・返却・照合
- **Out of scope:** challenge 以外の registration / authentication verification、session 実装方式、storage 製品、attestation、signature counter
- **Primary sources:** W3C Web Authentication: An API for accessing Public Key Credentials Level 3 §5.4.1、§5.4.2、§5.8.1、§7.1、§7.2、§13.4.3
- **Diagram:** RP が challenge を生成して Client に渡し、`clientDataJSON` 内の challenge を受け取って照合する縦方向 sequence diagram

## 1. `challenge` は RP が生成する

WebAuthn Level 3 §13.4.3 は、`PublicKeyCredentialCreationOptions.challenge` と `PublicKeyCredentialRequestOptions.challenge` の両方について、Relying Party が信頼する環境（例: server-side）でランダムに生成しなければならないと定めています（**MUST**）。

同 section は、challenge に推測を実行不可能にするだけの entropy が含まれなければならないことも **MUST** としています。また challenge は少なくとも 16 bytes とすることが **SHOULD** とされています。

challenge の有効期間については、WebAuthn ceremony timeout の推奨範囲の上限と同程度の期間を有効とすることが **SHOULD** とされています（§13.4.3）。

## 2. registration と authentication のどちらでも options の member に置く

`challenge` は HTTP query parameter や HTTP header ではありません。WebAuthn API に渡す options object の member です。

registration では `PublicKeyCredentialCreationOptions.challenge`、authentication では `PublicKeyCredentialRequestOptions.challenge` に `BufferSource` として置かれます（§5.4.1、§5.4.2）。

以下は配置だけを示す非規範的な最小例です。値は illustrative value です。

```javascript
// 非規範的な例: registration
const creationOptions = {
  publicKey: {
    challenge: registrationChallenge,
    rp: { name: "Example RP" },
    user: {
      id: userId,
      name: "user@example.test",
      displayName: "Example User"
    },
    pubKeyCredParams: [{ type: "public-key", alg: -7 }]
  }
};

await navigator.credentials.create(creationOptions);
```

```javascript
// 非規範的な例: authentication
const requestOptions = {
  publicKey: {
    challenge: authenticationChallenge
  }
};

await navigator.credentials.get(requestOptions);
```

`challenge` の型はどちらも `BufferSource` です。上の例は WebAuthn API 上の配置を示すためのものであり、RP server から browser へ options を配送する HTTP API の形式は WebAuthn 仕様の範囲外です。

## 3. Client は challenge を `clientDataJSON` に反映する

CollectedClientData の `challenge` member は DOMString で、RP が提供した challenge の base64url encoding を格納します（§5.8.1）。

概念的な構造を確認するための非規範的な例は次のとおりです。これは decoded `clientDataJSON` のうち、この記事のテーマに必要な member だけを示しています。

```json
{
  "type": "webauthn.get",
  "challenge": "illustrativeBase64urlChallenge",
  "origin": "https://example.test"
}
```

`type` と `origin` も CollectedClientData に定義された member ですが、それらの検証要件はこの記事では扱いません。

## 4. RP は返された challenge を生成済みの値と照合する

registration の検証手順では、RP は `clientDataJSON` を UTF-8 decode して JSON を parse した後、`C.challenge` が `pkOptions.challenge` の base64url encoding と等しいことを検証します（§7.1 step 8）。

authentication でも同じ対応関係を検証します。§7.2 step 11 は、`C.challenge` が `pkOptions.challenge` の base64url encoding と等しいことを検証するよう定めています。

§13.4.3 は、Client response で返された challenge が生成済み challenge と一致しなければならないことを **MUST** としています。また、この照合を Client の挙動に依存しない方法で行うこと、たとえば ceremony 完了まで RP が challenge を一時保存することを **SHOULD** としています。

<pre class="mermaid">
sequenceDiagram
    participant RP as Relying Party
    participant C as Client
    RP->>RP: challenge をランダム生成
    RP->>C: options.challenge
    C-->>RP: clientDataJSON
    RP->>RP: challenge を照合
</pre>

この図は challenge の生成・受け渡し・照合だけを示しています。Authenticator の署名処理や RP のその他の verification step は省略しています。

## 5. challenge mismatch を許容しない

§13.4.3 は Web Authentication が replay attack を避けるために randomized challenge に依存していると説明しています。生成した challenge と返却された challenge の mismatch を許容すると protocol の security が損なわれると明記されています。

ここで重要なのは、Client が返した任意の challenge を検証対象として受け入れるのではなく、**その ceremony のために RP が生成した challenge** と対応付けることです。

仕様は challenge の一時保存方法や session data model といった deployment-specific な実装を一つに固定していません。この記事でも特定の保存方式は推奨しません。

## まとめ

WebAuthn の registration と authentication では、RP が信頼する環境でランダムな challenge を生成し、WebAuthn options の `challenge` member として Client に渡します。Client はその値の base64url encoding を `clientDataJSON.challenge` に含めます。

RP は response を受け取った後、`clientDataJSON.challenge` がその ceremony で生成した challenge の base64url encoding と一致することを検証します。challenge の生成と一致確認はいずれも WebAuthn Level 3 §13.4.3 の **MUST** です。

**The challenge is RP-generated ceremony state, not a value the RP learns from the response.**  
（challenge は RP が ceremony のために生成する状態であり、response を受け取って初めて知る値ではありません。）

## 一次資料

- W3C, *Web Authentication: An API for accessing Public Key Credentials Level 3*, §5.4.1 PublicKeyCredentialCreationOptions, §5.4.2 PublicKeyCredentialRequestOptions, §5.8.1 Client Data Used in WebAuthn Signatures, §7.1 Registering a New Credential, §7.2 Verifying an Authentication Assertion, §13.4.3 Cryptographic Challenges: https://www.w3.org/TR/webauthn-3/
