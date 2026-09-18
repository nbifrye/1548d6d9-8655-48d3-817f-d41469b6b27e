---
layout: post
title: "WebAuthn Level 3：登録・認証セレモニーと Relying Party の検証手順"
date: 2026-09-18 09:00:00 +0900
categories: [authentication, webauthn]
---

Web Authentication (WebAuthn) Level 3 は、2026年8月25日付の **W3C Recommendation** です。W3C の仕様本文は、Web アプリケーションが公開鍵クレデンシャルを作成・利用し、ユーザーを強く認証するための API を定義しています。Level 3 は WebAuthn Level 2 の後継仕様です。

この記事では、W3C Recommendation に記載された登録（registration）と認証（authentication）の処理を、Relying Party（RP）から見た順序に沿って整理します。本文中の MUST / SHOULD / MAY は、仕様本文の規範語の強度を変えずに記載します。

## 1. WebAuthn を構成する主体

WebAuthn の処理には、主に次の主体が登場します。

| 主体 | 仕様上の役割 |
|---|---|
| Relying Party (RP) | 公開鍵クレデンシャルを利用してユーザーを認証する Web サービス |
| User Agent | Web Authentication API を Web アプリケーションへ公開し、Authenticator へのアクセスを仲介する |
| Authenticator | 公開鍵クレデンシャルを作成・保持し、ユーザーの同意の下で署名処理を行う |
| User | 登録または認証セレモニーに参加する利用者 |

WebAuthn の公開鍵クレデンシャルは RP ID にスコープされます。仕様 §4 では、RP ID は WebAuthn Relying Party を識別する有効なドメイン文字列として定義され、クレデンシャルは登録時と同じ RP ID に対してのみ認証に使用できます。

Web コンテキストでは、RP ID の既定値は呼び出し元 origin の effective domain です。呼び出し側が RP ID を指定する場合、その値は origin の effective domain と同一、または registrable domain suffix である必要があります。WebAuthn API は secure context に公開されます。

## 2. 登録セレモニー

登録では、RP が `PublicKeyCredentialCreationOptions` を作成し、User Agent が `navigator.credentials.create()` を実行します。Authenticator は新しい公開鍵クレデンシャルを作成し、User Agent は `PublicKeyCredential` を RP に返します。RP は仕様 §7.1 の手順で応答を検証し、credential record を保存します。

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

### 2.1 RP が渡す主なデータ

`PublicKeyCredentialCreationOptions` には、RP、ユーザー、challenge、利用可能な公開鍵アルゴリズムなどが含まれます。登録セレモニーは RP が `CredentialCreationOptions` を構成し、`navigator.credentials.create()` を呼び出すところから始まります。

challenge はクライアントデータへ含まれ、RP は登録応答の検証時に、返された `clientDataJSON` 内の challenge が、登録開始時に渡した challenge の base64url encoding と一致することを確認します。

### 2.2 Authenticator が生成するもの

Authenticator はユーザーの同意を得た後、仕様で選択された公開鍵アルゴリズムに従って新しい鍵ペアを生成します。credential source には、credential ID、秘密鍵、RP ID、user handle などが関連付けられます。

登録応答の attestation object は CBOR map であり、少なくとも次の要素を持ちます。

- `authData`: authenticator data
- `fmt`: attestation statement format identifier
- `attStmt`: attestation statement

Authenticator data には RP ID の SHA-256 ハッシュである `rpIdHash`、flags、signature counter、登録時には attested credential data などが含まれます。

## 3. RP による登録応答の検証

WebAuthn Level 3 §7.1 は、RP が登録時に実行する検証手順を規定しています。主要な検証項目は次のとおりです。

| 検証対象 | 仕様上の確認内容 |
|---|---|
| response type | `AuthenticatorAttestationResponse` であること |
| `clientDataJSON.type` | `webauthn.create` であること |
| `clientDataJSON.challenge` | RP が渡した challenge の base64url encoding と一致すること |
| `clientDataJSON.origin` | RP が期待する origin であること |
| `crossOrigin` / `topOrigin` | cross-origin iframe を使用する場合、RP が期待する条件と一致すること |
| `rpIdHash` | RP が期待する RP ID の SHA-256 ハッシュと一致すること |
| UP flag | conditional mediation でない場合、User Presence が設定されていること |
| UV flag | RP が user verification を要求した場合、User Verification が設定されていること |
| BE / BS flags | backup eligibility / backup state の組み合わせが仕様の条件を満たすこと |
| 公開鍵アルゴリズム | credential public key の `alg` が RP の `pubKeyCredParams` に含まれること |
| attestation | `fmt` に対応する verification procedure に従って検証すること |
| credential ID | 1023 bytes 以下であることを検証し、既存登録との重複も検証すること |

RP は `clientDataJSON` を UTF-8 としてデコードし、JSON として解析します。その後、`type`、`challenge`、`origin` を順に検証します。登録応答に `topOrigin` が含まれる場合、RP は cross-origin iframe の利用を期待していること、および `topOrigin` が期待する上位ページの origin と一致することを検証します。

attestation については、RP は `attestationObject` を CBOR decode し、`fmt`、`authData`、`attStmt` を取得します。続いて `fmt` に対応する attestation statement format の verification procedure を実行します。attestation trust path を利用する場合、仕様は RP が受容可能な trust anchor を取得し、証明書チェーンを検証する手順を定めています。

## 4. 登録後に保存する credential record

Level 3 §7.1 は、登録検証が成功した後に作成する credential record を明示しています。仕様に列挙される項目は次のとおりです。

| 項目 | 内容 |
|---|---|
| `type` | PublicKeyCredential の type |
| `id` | credential ID |
| `publicKey` | credential public key |
| `signCount` | authenticator data の signature counter |
| `uvInitialized` | 登録時の UV flag |
| `transports` | `getTransports()` の戻り値 |
| `backupEligible` | BE flag |
| `backupState` | BS flag |

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
    RP->>RP: signCount 等を処理
</pre>

`PublicKeyCredentialRequestOptions.challenge` は必須です。RP が `allowCredentials` を指定した場合、認証応答の credential ID が、そのリストに含まれる credential を識別することを検証します。

## 6. RP による認証 assertion の検証

Level 3 §7.2 の主要な検証手順は次のとおりです。

1. 応答が `AuthenticatorAssertionResponse` であることを確認する。
2. `allowCredentials` が空でなければ、返された credential ID がそのリストに含まれることを確認する。
3. credential ID と user handle を使って、登録済み credential record とユーザーを特定する。
4. `clientDataJSON.type` が `webauthn.get` であることを確認する。
5. `clientDataJSON.challenge` が要求時の challenge と一致することを確認する。
6. `clientDataJSON.origin` が RP の期待する origin であることを確認する。
7. 必要に応じて `crossOrigin` と `topOrigin` を確認する。
8. authenticator data の `rpIdHash` が期待する RP ID の SHA-256 ハッシュと一致することを確認する。
9. UP flag が設定されていることを確認する。
10. user verification が必要な場合は UV flag が設定されていることを確認する。
11. `clientDataJSON` の SHA-256 ハッシュを計算する。
12. 登録済み credential public key を使い、`authenticatorData || SHA-256(clientDataJSON)` に対する signature を検証する。
13. signature counter が使用されている場合は、登録済み `signCount` と今回の値を比較する。
14. extension outputs を処理する。

signature counter について、仕様 §7.2 は今回の値が保存済み値以下である場合を、Authenticator が clone された可能性を示す **signal ではあるが proof ではない** と説明しています。仕様は、その場合に認証を失敗させるか、counter を更新するかなどを RP 固有の判断として扱っています。

## 7. Level 3 で追加・変更された項目

Level 3 の Revision History §18.1 は、Level 2 からの変更を列挙しています。新機能として、次の項目などが記載されています。

- `PublicKeyCredential.toJSON()`
- `parseCreationOptionsFromJSON()`
- `parseRequestOptionsFromJSON()`
- cross-origin iframe での create operation
- create / get における conditional mediation
- `getClientCapabilities()`
- authenticator transport の `hybrid`
- credential changes を Authenticator へ通知する signal methods
- client data の `topOrigin`
- related origins をまたぐ WebAuthn 利用
- authenticator data の BE / BS flags
- compound attestation statement format
- `prf` extension
- registration parameter `attestationFormats`

また、Android SafetyNet Attestation Statement Format は deprecated として列挙され、`tokenBinding` は reserved に変更されています。

## 8. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)
- W3C publication history: [WebAuthn Level 3 publication history](https://www.w3.org/standards/history/webauthn-3/)
- W3C announcement: [Web Authentication Level 3 is now a W3C Recommendation](https://www.w3.org/news/2026/web-authentication-an-api-for-accessing-public-key-credentials-level-3-is-now-a-w3c-recommendation/)

参照した主要節: §4, §5.5, §6.1, §6.5, §7.1, §7.2, §13.4.9, §18.1  
最終確認: 2026-09-18
