---
layout: post
title: "WebAuthn Level 3：conditional mediation の認証フローはどう進むのか"
date: 2026-09-19 22:39:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** WebAuthn RP / frontend 実装者  
**この記事で伝えること:** `navigator.credentials.get()` で `mediation: "conditional"` を指定した認証要求について、利用可否の確認、credential discovery、ユーザーによる credential 選択、assertion 取得までの処理を WebAuthn Level 3 に沿って追えること  
**扱わないこと:** conditional mediation を使う登録、通常の `required` / `optional` / `silent` mediation、RP による assertion の一般的な検証手順、Related Origin Requests、Authenticator 内部の CTAP 処理

この記事は WebAuthn Level 3 の conditional mediation のうち、**authentication ceremony (`navigator.credentials.get()`)** に範囲を限定します。

## Article brief

- **Reader:** conditional mediation を使った WebAuthn 認証を実装・レビューする RP / frontend 実装者
- **Question:** `mediation: "conditional"` を指定したとき、通常の credential request と比べて Client はどのように credential を探索し、いつ Authenticator に request を発行するのか
- **Answer:** RP が capability を確認し、`navigator.credentials.get()` を conditional mediation で開始した後、Client が discoverable credential の metadata を収集し、ユーザーの UI interaction と credential 選択を契機に Authenticator へ request を発行する流れを説明する
- **Scope:** WebAuthn Level 3 §5.1.4、§5.1.7、§5.8.7 に定義された authentication の conditional mediation
- **Out of scope:** conditional registration、RP assertion validation の全手順、UI の具体的な見た目、passkey の同期方式、CTAP の詳細
- **Primary sources:** W3C Web Authentication: An API for accessing Public Key Credentials Level 3 §5.1.4、§5.1.7、§5.8.7
- **Diagram:** capability check から credential selection、Authenticator request までの縦方向 flowchart

## 1. 最初に conditional mediation の利用可否を確認する

WebAuthn Level 3 §5.1.2 の `PublicKeyCredential.isConditionalMediationAvailable()` は、`navigator.credentials.get()` で conditional mediation が利用可能かを示します。呼び出し結果は Promise で、利用可能なら `true`、そうでなければ `false` に resolve します。

RP は `mediation` を `conditional` に設定する前に、この利用可否を確認することが **SHOULD** とされています（§5.1.2）。

Level 3 §5.8.7 では `conditionalGet` Client capability も定義されています。`conditionalGet` が `true` であることは、`isConditionalMediationAvailable()` が `true` に resolve することと同等です。§5.1.7 では、RP は user-visible error を避けるため、`isConditionalMediationAvailable()` または `getClientCapabilities()` を使って `conditionalGet` capability を確認することが **SHOULD** とされています。

以下は配置を示す非規範的な例です。

```javascript
// 非規範的な例
const available =
  await PublicKeyCredential.isConditionalMediationAvailable();

if (available) {
  const credential = await navigator.credentials.get({
    publicKey: requestOptions,
    mediation: "conditional"
  });
}
```

`mediation` は `PublicKeyCredentialRequestOptions` の member ではなく、`navigator.credentials.get()` に渡す `CredentialRequestOptions` 側の member です。`publicKey` に WebAuthn の request options を置き、その隣に `mediation: "conditional"` を指定します。

## 2. conditional request を開始すると Client は何を変えるか

WebAuthn Level 3 §5.1.4 の `[[DiscoverFromExternalSource]]` algorithm では、`mediation` が `conditional` の場合、Client はまず `PublicKeyCredentialRequestOptions.allowCredentials` の値を `credentialIdFilter` として保持し、その後 `allowCredentials` を空にします。

仕様の Note は、この処理によって conditional request で non-discoverable credentials が使用されることを防ぐと説明しています。

また、conditional mediation の場合、algorithm の lifetime timer は infinity に設定されます（§5.1.4）。これは conditional request の Client algorithm 上の処理であり、RP が独自の timeout 値を無限に設定するという意味ではありません。

## 3. Client は discoverable credential の metadata を収集する

利用可能になった Authenticator が `silentCredentialDiscovery` operation をサポートする場合、Client は conditional mediation でその operation を `rpId` とともに呼び出します（§5.1.4）。

返された discoverable credential metadata について、最初に保存した `credentialIdFilter` が空であるか、metadata の credential ID が filter に含まれる場合、Client はその metadata を `silentlyDiscoveredCredentials` に保持します。

この段階で仕様が扱うのは credential metadata の discovery です。Authenticator への assertion request は、後述するユーザー選択を契機として発行されます。

## 4. ユーザーの UI interaction から credential request へ進む

WebAuthn Level 3 §5.1.4 は、conditional request 中にユーザーが `autocomplete` の non-autofill credential type が `"webauthn"` である `input` または `textarea` と interaction した場合の処理を定義しています。

HTML の配置を示す非規範的な最小例は次のとおりです。

```html
<!-- 非規範的な例 -->
<input name="username" autocomplete="username webauthn">
```

仕様の Note によれば、`webauthn` autofill detail token は Normal または Contact 型の最後の autofill detail token の直後に置かれます。仕様は例として `"username webauthn"` を示しています。

Client はこの UI context で、収集済みの discoverable credential metadata からユーザーに credential を選択させます。ユーザーが credential を選択すると、Client はその credential ID を一時的な `PublicKeyCredentialRequestOptions.allowCredentials` に設定し、対応する Authenticator に credential request を発行します（§5.1.4）。

<pre class="mermaid">
flowchart TD
    A[conditionalGet capability を確認] --> B[credentials.get を開始]
    B --> C[discoverable credential metadata を収集]
    C --> D[ユーザーが webauthn 対応 UI と interaction]
    D --> E[ユーザーが credential を選択]
    E --> F[Authenticator に credential request]
    F --> G[assertion を取得]
</pre>

図は §5.1.4 の conditional authentication に関係する処理だけを抜き出しています。

## 5. `allowCredentials` が指定されていても discovery 時には空にされる

conditional mediation では、RP が元の `PublicKeyCredentialRequestOptions` に `allowCredentials` を指定していた場合でも、その値は discovery の前に `credentialIdFilter` として退避され、`pkOptions.allowCredentials` 自体は空にされます（§5.1.4）。

その後、silent discovery で得た credential metadata は、元の filter が空か、その credential ID が filter に含まれる場合に `silentlyDiscoveredCredentials` へ追加されます。ユーザーが credential を選択した段階で、その ID を含む一時的な `allowCredentials` list が作られ、Authenticator への request に使われます。

したがって、元の `allowCredentials` は conditional mediation で無視されるのではなく、discovery 結果を絞り込む filter として algorithm 内で扱われます。

## 6. conditional mediation が規定しないもの

conditional mediation は、RP が assertion を受け取った後の一般的な authentication verification を置き換えるものではありません。RP の assertion verification は WebAuthn Level 3 §7.2 に別途定義されています。

また、ユーザーに credential をどのような視覚表現で提示するかなど、仕様が Client platform 固有の処理としている事項について、この記事では特定の UI を規定しません。

`isConditionalMediationAvailable()` は `navigator.credentials.get()` の conditional mediation の利用可否を示す API です。conditional registration の利用可否を示すものではなく、Level 3 はそのために `getClientCapabilities()` の `conditionalCreate` capability を定義しています（§5.1.2、§5.8.7）。conditional registration はこの記事の範囲外です。

## まとめ

WebAuthn Level 3 の conditional authentication では、RP は `mediation: "conditional"` を指定して `navigator.credentials.get()` を開始します。RP はその前に conditional mediation の availability を確認することが SHOULD とされています。

Client は conditional request で discoverable credential metadata を収集し、`webauthn` autocomplete token に対応する UI interaction とユーザーの credential 選択を経て、選択された credential を対象に Authenticator へ request を発行します。

**Conditional mediation changes when credential discovery becomes an authenticator request; it does not replace WebAuthn assertion verification.**  
（conditional mediation が変えるのは credential discovery から Authenticator request へ進むタイミングであり、WebAuthn assertion の検証そのものを置き換えるものではありません。）

## 一次資料

- W3C, *Web Authentication: An API for accessing Public Key Credentials Level 3*, §5.1.2 `isConditionalMediationAvailable()`, §5.1.4 Use an Existing Credential to Make an Assertion, §5.1.7 Availability of client capabilities, §5.8.7 Client Capability Enumeration: https://www.w3.org/TR/webauthn-3/
