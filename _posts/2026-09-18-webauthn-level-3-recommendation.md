---
layout: post
title: "WebAuthn Level 3：Relying Party から見る登録・認証セレモニーの検証"
date: 2026-09-18 09:00:00 +0900
categories: [authentication, webauthn]
---

Web Authentication (WebAuthn) Level 3 は、2026年8月25日付の W3C Recommendation です。

## この記事について

**記事タイプ:** Flow / Requirement  
**対象読者:** WebAuthn を利用する Relying Party（RP）の実装・レビューを担当する開発者  
**この記事で伝えること:** 登録と認証の各セレモニーで、RP が何を受け取り、どの値をどの順序で検証するか  
**扱わないこと:** passkey の同期方式、アカウント復旧設計、各 attestation format の詳細、WebAuthn extensions の個別仕様

この記事は、WebAuthn Level 3 の全機能を紹介するものではありません。RP の実装に直接関係する **登録（registration）と認証（authentication）の検証処理** に範囲を限定し、W3C Recommendation §7.1 と §7.2 を中心に整理します。

## 1. RP が関与する処理の全体像

WebAuthn の処理には、Relying Party、User Agent、Authenticator、User が登場します。

- **Relying Party (RP):** 公開鍵クレデンシャルを利用してユーザーを認証する Web サービス。
- **User Agent:** Web Authentication API を Web アプリケーションへ公開し、Authenticator へのアクセスを仲介する。
- **Authenticator:** 公開鍵クレデンシャルを作成・保持し、ユーザーの同意の下で署名処理を行う。
- **User:** 登録または認証セレモニーに参加する利用者。

RP の処理は大きく2つに分かれます。

1. 登録時に、新しい公開鍵クレデンシャルを受け取り、その内容を検証して credential record を保存する。
2. 認証時に、Authenticator が作成した assertion を受け取り、登録済み公開鍵を使って検証する。

<pre class="mermaid">
flowchart TD
    A[登録開始] --> B[PublicKeyCredentialCreationOptions]
    B --> C[Authenticator が credential を作成]
    C --> D[RP が §7.1 に従って検証]
    D --> E[credential record を保存]
    E --> F[認証開始]
    F --> G[PublicKeyCredentialRequestOptions]
    G --> H[Authenticator が assertion を生成]
    H --> I[RP が §7.2 に従って検証]
</pre>

## 2. 登録セレモニー

登録では、RP が `PublicKeyCredentialCreationOptions` を作成し、User Agent が `navigator.credentials.create()` を実行します。Authenticator は新しい公開鍵クレデンシャルを作成し、User Agent は `PublicKeyCredential` を RP に返します。

<pre class="mermaid">
sequenceDiagram
    participant RP as Relying Party
    participant UA as User Agent
    participant A as Authenticator
    RP->>RP: challenge と PublicKeyCredentialCreationOptions を生成
    RP->>UA: navigator.credentials.create(options)
    UA->>A: credential creation request
    A->>A: user consent / 必要に応じ user verification
    A->>A: 公開鍵・秘密鍵の組を生成
    A-->>UA: authenticator data + attestation
    UA-->>RP: PublicKeyCredential
    RP->>RP: §7.1 の検証手順
    RP->>RP: credential record を保存
</pre>

### 2.1 RP ID と origin

WebAuthn の公開鍵クレデンシャルは RP ID にスコープされます。仕様 §4 では、RP ID は WebAuthn Relying Party を識別する有効なドメイン文字列として定義されています。

Web コンテキストでは、RP ID の既定値は呼び出し元 origin の effective domain です。呼び出し側が RP ID を指定する場合、その値は origin の effective domain と同一、または registrable domain suffix である必要があります。

### 2.2 challenge

`PublicKeyCredentialCreationOptions` には challenge が含まれます。登録応答の検証時、RP は `clientDataJSON` に含まれる challenge が、登録開始時に渡した challenge の base64url encoding と一致することを確認します。

### 2.3 Authenticator が返すデータ

登録応答の attestation object は CBOR map で、少なくとも次の要素を含みます。

- `authData`: authenticator data
- `fmt`: attestation statement format identifier
- `attStmt`: attestation statement

Authenticator data には `rpIdHash`、flags、signature counter、および登録時には attested credential data が含まれます。

## 3. 登録時に RP が検証する項目

WebAuthn Level 3 §7.1 は、RP が登録応答に対して実行する verification procedure を定義しています。

検証項目は次のとおりです。

1. response が `AuthenticatorAttestationResponse` であること。
2. `clientDataJSON.type` が `webauthn.create` であること。
3. `clientDataJSON.challenge` が登録開始時の challenge と一致すること。
4. `clientDataJSON.origin` が RP の期待する origin であること。
5. `crossOrigin` / `topOrigin` が、cross-origin 利用時の RP の期待値と一致すること。
6. `rpIdHash` が期待する RP ID の SHA-256 ハッシュと一致すること。
7. 仕様が要求する条件で UP flag が設定されていること。
8. RP が user verification を要求した場合、UV flag が設定されていること。
9. BE / BS flags の組み合わせが仕様に適合すること。
10. credential public key の `alg` が `pubKeyCredParams` に含まれること。
11. attestation を `fmt` に対応する verification procedure で検証すること。
12. credential ID が仕様の長さと重複条件を満たすこと。

RP は `clientDataJSON` を UTF-8 としてデコードし、JSON として解析したうえで、`type`、`challenge`、`origin` などを検証します。

attestation については、RP は `attestationObject` を CBOR decode し、`fmt`、`authData`、`attStmt` を取得します。その後、`fmt` に対応する attestation statement format の verification procedure を実行します。

## 4. 登録後に RP が保存する credential record

WebAuthn Level 3 は、§7 の手順を実装するため、Relying Party が登録済み public key credential source の一部の属性を保持することを要求しています（MUST）。

そのうえで、仕様は次の項目を credential record に保持することを推奨しています（RECOMMENDED）。

- **`type`:** PublicKeyCredential の type
- **`id`:** credential ID
- **`publicKey`:** credential public key
- **`signCount`:** authenticator data の signature counter
- **`uvInitialized`:** 登録時の UV flag
- **`transports`:** `getTransports()` の戻り値
- **`backupEligible`:** BE flag
- **`backupState`:** BS flag

`attestationObject`、登録時の `clientDataJSON`、RP ID などは OPTIONAL な保存項目として列挙されています。

## 5. 認証セレモニー

認証では、RP が `PublicKeyCredentialRequestOptions` を構成し、User Agent が `navigator.credentials.get()` を実行します。Authenticator は選択された credential private key を使って assertion signature を生成し、RP は登録時に保存した credential public key を使って署名を検証します。

<pre class="mermaid">
sequenceDiagram
    participant RP as Relying Party
    participant UA as User Agent
    participant A as Authenticator
    RP->>RP: challenge と PublicKeyCredentialRequestOptions を生成
    RP->>UA: navigator.credentials.get(options)
    UA->>A: assertion request
    A->>A: user presence / 必要に応じ user verification
    A->>A: authenticatorData と clientDataHash を対象に署名
    A-->>UA: assertion
    UA-->>RP: AuthenticatorAssertionResponse
    RP->>RP: type / challenge / origin / rpIdHash / flags を検証
    RP->>RP: 登録済み公開鍵で signature を検証
</pre>

## 6. 認証時に RP が検証する項目

Level 3 §7.2 は、RP の verification procedure を次の順序で規定しています。

1. 応答が `AuthenticatorAssertionResponse` であることを確認する。
2. `allowCredentials` が空でなければ、返された credential ID がそのリストに含まれることを確認する。
3. credential ID と user handle を使って、登録済み credential record とユーザーを特定する。
4. `clientDataJSON.type` が `webauthn.get` であることを確認する。
5. `clientDataJSON.challenge` が要求時の challenge と一致することを確認する。
6. `clientDataJSON.origin` が RP の期待する origin であることを確認する。
7. 必要に応じて `crossOrigin` と `topOrigin` を確認する。
8. `rpIdHash` が期待する RP ID の SHA-256 ハッシュと一致することを確認する。
9. UP flag を確認する。
10. user verification が必要な場合は UV flag を確認する。
11. `clientDataJSON` の SHA-256 ハッシュを計算する。
12. 登録済み credential public key を使い、`authenticatorData || SHA-256(clientDataJSON)` に対する signature を検証する。
13. signature counter を使用する場合は、保存済み `signCount` と今回の値を比較する。
14. extension outputs を処理する。

signature counter について、§7.2 は今回の値が保存済み値以下である場合を、Authenticator が clone された可能性を示す signal ではあるが proof ではないと説明しています。その後の処理は RP の判断に委ねられています。

## 7. このテーマで押さえる範囲

この記事の主題は、RP が WebAuthn の登録・認証結果を検証する処理です。attestation format の種類、conditional mediation、related origins、`prf` など Level 3 の個別機能は、§7.1 / §7.2 の検証フローを理解するために必要な範囲を除き扱っていません。

## 8. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)
- W3C publication history: [WebAuthn Level 3 publication history](https://www.w3.org/standards/history/webauthn-3/)

参照した主要節: §4, §5.5, §6.1, §6.5, §7.1, §7.2  
最終確認: 2026-09-19
