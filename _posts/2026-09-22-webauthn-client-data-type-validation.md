---
layout: post
title: "WebAuthn の clientDataJSON.type：registration と authentication を識別する"
date: 2026-09-22 16:46:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** WebAuthn の registration / authentication response をサーバー側で検証する Relying Party（RP）の実装・レビュー担当者  
**この記事で伝えること:** `clientDataJSON.type` の値が ceremony ごとに異なり、RP が registration では `webauthn.create`、authentication では `webauthn.get` を検証すること  
**扱わないこと:** challenge、origin、`crossOrigin` / `topOrigin`、RP ID、UP / UV、signature、attestation、credential selection

WebAuthn の `clientDataJSON` には `type` member があり、credential creation では `webauthn.create`、assertion generation では `webauthn.get` が入ります。RP の verification procedure は、この値を ceremony に対応する文字列と照合します。本記事は W3C Web Authentication Level 3 §5.8.1、§7.1、§7.2 に範囲を限定します。

## 1. type は CollectedClientData の JSON member

§5.8.1 は `CollectedClientData.type` を DOMString として定義しています。新しい credential を作成するときの値は `webauthn.create`、既存 credential から assertion を取得するときの値は `webauthn.get` です。同節は、この member の目的を、正当な signature を別の用途へ置き換える種類の signature confusion attack を防ぐことと説明しています。

### 非規範的な構造例

次は `type` の配置を確認するための非規範的な例です。`challenge` と `origin` の値は illustrative であり、本記事ではそれらの validation rule を扱いません。

Registration の decoded `clientDataJSON`:

```json
{
  "type": "webauthn.create",
  "challenge": "illustrative-challenge",
  "origin": "https://login.example"
}
```

Authentication の decoded `clientDataJSON`:

```json
{
  "type": "webauthn.get",
  "challenge": "illustrative-challenge",
  "origin": "https://login.example"
}
```

- `type`: DOMString。
- 配置: `AuthenticatorResponse.clientDataJSON` を UTF-8 decode し、JSON parse して得る client data の member。
- Registration の値: `webauthn.create`。
- Authentication の値: `webauthn.get`。

## 2. registration では webauthn.create を検証する

Registration verification では、RP は `response.clientDataJSON` を UTF-8 decode し、JSON parser で client data `C` を得ます（§7.1 steps 5–6）。続く §7.1 step 7 は、`C.type` の値が `webauthn.create` であることを検証する手順を定めています。

**Registration verification expects `clientDataJSON.type` to be `webauthn.create`.**  
（Registration の検証では、`clientDataJSON.type` が `webauthn.create` であることを確認します。）

## 3. authentication では webauthn.get を検証する

Authentication assertion の verification でも、RP は `clientDataJSON` を UTF-8 decode して JSON parse します（§7.2 steps 8–9）。§7.2 step 10 は、`C.type` の値が文字列 `webauthn.get` であることを検証する手順を定めています。

**Authentication verification expects `clientDataJSON.type` to be `webauthn.get`.**  
（Authentication の検証では、`clientDataJSON.type` が `webauthn.get` であることを確認します。）

<pre class="mermaid">
flowchart TD
    A[clientDataJSON] --> B[UTF-8 decode]
    B --> C[JSON parse]
    C --> D{Ceremony}
    D -->|Registration| E[type = webauthn.create]
    D -->|Authentication| F[type = webauthn.get]
    E --> G[後続の検証へ]
    F --> G
</pre>

この図は §7.1 と §7.2 の `type` verification に対応する非規範的な要約です。

## 4. type と challenge / origin は別々に検証される

Registration では §7.1 steps 7–9 が `type`、`challenge`、`origin` を順に検証します。Authentication では §7.2 steps 10–12 が同様にそれぞれを検証します。

したがって `type` の照合は challenge validation や origin validation の代替ではありません。本記事では `type` だけを中心テーマとし、challenge と origin の要件は扱いません。

## 5. Article brief

- **Reader:** WebAuthn registration / authentication response の server-side verification を実装・レビューする RP 担当者。
- **Question:** `clientDataJSON.type` には何が入り、registration と authentication で RP は何を検証するのか。
- **Answer:** `type` の配置と、registration の `webauthn.create`、authentication の `webauthn.get` という ceremony-specific verification を理解できる。
- **Scope:** §5.8.1 の `CollectedClientData.type`、§7.1 step 7、§7.2 step 10。
- **Out of scope:** challenge、origin、`crossOrigin` / `topOrigin`、RP ID、UP / UV、signature、attestation、credential selection。
- **Primary sources:** W3C Web Authentication Level 3 §5.8.1, §7.1, §7.2。
- **Diagram:** decoded client data から ceremony ごとの expected `type` を照合する縦方向 flowchart。

## 6. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §5.8.1, §7.1, §7.2  
最終確認: 2026-09-22
