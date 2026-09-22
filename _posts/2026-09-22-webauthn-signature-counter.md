---
layout: post
title: "WebAuthn の signature counter：signCount の比較と RP の処理"
date: 2026-09-22 14:41:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Security Practice / Requirement  
**対象読者:** WebAuthn authentication assertion をサーバー側で検証し、credential record を管理する Relying Party（RP）の実装・レビュー担当者  
**この記事で伝えること:** `signCount` が authenticator data のどこにあり、RP が保存値とどのように比較し、non-increasing value を仕様上どう解釈するか  
**扱わないこと:** challenge、origin、RP ID、user verification、backup state、signature algorithm、attestation、具体的な risk policy の設計

WebAuthn Level 3 の authenticator data には `signCount` が含まれます。Authenticator が signature counter を実装する場合、その値は successful `authenticatorGetAssertion` ごとに正の値だけ増加します。一方、counter を実装しない Authenticator は `signCount` を常に 0 のままにします。本記事は W3C Recommendation §6.1、§6.1.1、§6.3.2、§6.3.3、§7.1、§7.2 に範囲を限定します。

## 1. signCount は authenticator data に入る

§6.1 では authenticator data を 37 bytes 以上の byte array として定義しています。先頭 32 bytes の `rpIdHash`、1 byte の `flags` に続く 4 bytes が `signCount` です。`signCount` は 32-bit unsigned big-endian integer です。

### 非規範的な構造例

次は配置を確認するための非規範的な例です。値は illustrative です。

```text
byte 0..31   rpIdHash   = <32-byte hash>
byte 32      flags      = <flags byte>
byte 33..36  signCount  = 0000002A  # illustrative: 42
```

`signCount` は JSON member や HTTP header ではありません。`AuthenticatorAssertionResponse.authenticatorData` に含まれる binary authenticator data の field です。

- `signCount`: 32-bit unsigned big-endian integer。
- authentication assertion では RP が `authenticatorData` を parse して取得します。
- counter 非対応の Authenticator では 0 のままです（§6.1.1）。

## 2. Authenticator の counter 処理

§6.1.1 では、Authenticator は signature counter feature を実装すべきです（**SHOULD**）。counter は credential ごと、または Authenticator 全体で保持できます。

同節は per-credential counter を実装すべきとしています（**SHOULD**）。global counter を実装してもよい（**MAY**）としています。また、counter value が hardware failure などによって偶発的に減少しないようにすべきです（**SHOULD**）。

§6.3.3 の `authenticatorGetAssertion` では、実装している credential-associated counter または global counter を正の値だけ increment します。counter を実装していない場合は 0 のままです。

**A zero signCount can mean that the authenticator does not implement a signature counter.**  
（`signCount` が 0 であることは、Authenticator が signature counter を実装していない場合があります。）

## 3. registration 時に RP が保存する値

§7.1 では registration verification の結果として credential record を作成し、その `signCount` に registration response の `authData.signCount` を保存します。

したがって、まだ authentication assertion を処理していない credential でも、RP 側には比較の基準となる `credentialRecord.signCount` が存在します。§6.1.1 も、最初の assertion より前は `authenticatorMakeCredential` で得た counter を保存値として扱うことを説明しています。

本記事では credential record の他の field は扱いません。

## 4. authentication では保存値と新しい値を比較する

§7.2 step 22 では、`authData.signCount` または `credentialRecord.signCount` のどちらかが nonzero の場合に counter comparison を行います。

<pre class="mermaid">
flowchart TD
    A[Authentication assertion] --> B[authData.signCount を取得]
    B --> C{新値または保存値が nonzero?}
    C -->|No| D[counter comparison なし]
    C -->|Yes| E{新値 > 保存値?}
    E -->|Yes| F[counter は valid]
    E -->|No| G[clone 等の signal]
    F --> H[後続処理]
    G --> H
</pre>

新しい `authData.signCount` が保存済み `credentialRecord.signCount` より大きい場合、signature counter は valid です。

新しい値が保存値以下の場合、それは Authenticator が clone されている可能性を示す signal ですが、proof ではありません。仕様はほかにも Authenticator の malfunction や、RP が assertion を生成順とは異なる順序で処理する race condition を例示しています（§7.2 step 22）。

**A non-increasing counter is a signal, not proof, of a cloned authenticator.**  
（増加していない counter は、Authenticator の clone を示す signal ではありますが、証明ではありません。）

## 5. mismatch 時の判断は RP-specific

§7.2 step 22 は、RP が自身の operational characteristics を評価し、この情報を risk scoring に組み込むべきとしています。non-increasing value の場合に `credentialRecord.signCount` を更新するか、更新しないか、authentication ceremony を失敗させるかどうかは **RP-specific** です。

したがって、仕様は「counter が増えなければ必ず authentication を拒否する」という一律の処理を要求していません。本記事でも特定の risk policy を推奨しません。

§6.1.1 も、counter mismatch だけでは現在の operation が clone と original のどちらで実行されたかは分からないと説明しています。

## 6. verification 後の signCount 更新

§7.2 step 24 では credential record の state update として、`credentialRecord.signCount` を `authData.signCount` の値に更新します。

ただし RP が WebAuthn ceremony steps に加えて追加の security checks を実施する場合、これらの state update は、その追加 check が成功した後まで defer すべきです（**SHOULD**, §7.2 step 24）。

この state update は、step 22 における mismatch 時の RP-specific な判断とあわせて読む必要があります。仕様は mismatch 時の update / rejection policy を一律には定めていません。

## 7. Article brief

- **Reader:** WebAuthn authentication assertion の server-side verification と credential record 管理を実装・レビューする RP 担当者。
- **Question:** `signCount` はどこにあり、RP は保存済み counter とどう比較し、増加していない値をどう解釈するのか。
- **Answer:** authenticator data 内の `signCount` の形式、Authenticator の counter behavior、registration 時の保存、authentication 時の comparison、non-increasing value が signal であって proof ではないこと、mismatch 時の判断が RP-specific であることを理解できる。
- **Scope:** authenticator data の `signCount`、§6.1.1 の signature counter considerations、§7.1 の初期保存、§7.2 の comparison と state update。
- **Out of scope:** challenge、origin、RP ID、UV / UP、BE / BS、signature verification の暗号詳細、attestation、具体的な risk scoring / rejection policy。
- **Primary sources:** W3C Web Authentication Level 3 §6.1, §6.1.1, §6.3.2, §6.3.3, §7.1, §7.2。
- **Diagram:** authentication assertion の `signCount` と credential record の保存値を比較し、valid / signal に分岐する縦方向 flowchart。

## 8. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §6.1, §6.1.1, §6.3.2, §6.3.3, §7.1, §7.2  
最終確認: 2026-09-22
