---
layout: post
title: "WebAuthn の BE / BS flags：credential backup eligibility と backup state"
date: 2026-09-22 12:45:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Feature Deep Dive / Requirement  
**対象読者:** WebAuthn の registration / authentication response を検証し、credential record を管理する Relying Party（RP）の実装・レビュー担当者  
**この記事で伝えること:** authenticator data の BE / BS flags が何を表し、どの組み合わせが有効で、registration と authentication で RP がどう扱うか  
**扱わないこと:** passkey の同期方式や backup service の実装、account recovery の設計、user verification、signature counter、attestation format の詳細

WebAuthn Level 3 では、credential の **backup eligibility** と現在の **backup state** を authenticator data の `BE` / `BS` flags で表します。本記事は W3C Recommendation §4、§6.1、§6.1.3、§7.1、§7.2 に範囲を限定します。

## 1. BE と BS は別の状態を表す

§4 と §6.1.3 では、backup eligibility と backup state を区別しています。

- **BE (Backup Eligibility):** public key credential source が backup 可能かどうかを表します。生成した Authenticator が credential 作成時に決定する credential property です。
- **BS (Backup State):** multi-device credential が現在 backed up されているかを表します。現在の managing authenticator が決定し、時間の経過とともに変化し得ます。

§6.1.3 により、BE の値は `authenticatorMakeCredential` operation で設定され、**MUST NOT** change です。一方、BS は public key credential source の現在の状態に応じて変化し得ます。

**BE is a permanent credential property; BS is current state.**  
（BE は永続的な credential property であり、BS は現在の状態です。）

## 2. authenticator data のどこに入るか

BE と BS は JSON member ではありません。§6.1 で定義される binary の authenticator data にある 1 byte の `flags` に格納されます。

- Bit 3: `BE`
- Bit 4: `BS`
- `BE=1`: public key credential source は backup eligible
- `BS=1`: public key credential source は現在 backed up

Authenticator は `BE` を、credential が multi-device credential である場合に、かつその場合に限って set します（**SHALL**, §6.1）。この値は registration ceremony 後に変えてはなりません（**MUST NOT**, §6.1）。

Authenticator は `BS` を、credential が multi-device credential で、かつ現在 backed up されている場合に、かつその場合に限って set します（**SHALL**, §6.1）。backup status が不確実、または backed up credential に問題があると Authenticator が疑う場合、`BS` は set すべきではありません（**SHOULD NOT**, §6.1）。

### 非規範的な構造例

次は配置を確認するための非規範的な例です。値は illustrative です。

```text
authenticator data
  bytes 0..31 : rpIdHash
  byte 32     : flags
  bytes 33..36: signCount

flags = 0x19
        00011001
           ^^ 
           ||
           |+-- bit 3 BE = 1
           +--- bit 4 BS = 1
```

この例では `BE=1` かつ `BS=1` です。`flags` byte には BE / BS 以外の flag も含まれるため、`0x19` 全体に BE / BS だけの意味があるわけではありません。

## 3. 有効な組み合わせ

§6.1.3 は BE / BS の組み合わせを次のように定義しています。

- **BE=0, BS=0:** single-device credential。
- **BE=0, BS=1:** 許可されない組み合わせ。
- **BE=1, BS=0:** multi-device credential で、現在は backed up されていない。
- **BE=1, BS=1:** multi-device credential で、現在 backed up されている。

したがって、`BS=1` は `BE=1` を伴います。

<pre class="mermaid">
flowchart TD
    A[authenticator data flags] --> B{BE}
    B -->|0| C{BS}
    C -->|0| D[single-device credential]
    C -->|1| E[許可されない]
    B -->|1| F{BS}
    F -->|0| G[multi-device / not backed up]
    F -->|1| H[multi-device / backed up]
</pre>

## 4. registration で RP が扱う値

§7.1 の registration verification では、RP が credential の backup eligibility を user experience flow や policy に利用する場合、`authData.flags` の BE bit を評価します（§7.1 step 18）。同様に backup state を利用する場合は BS bit を評価します（§7.1 step 19）。

WebAuthn Level 3 の credential record では `backupEligible` と `backupState` が定義されています。仕様は、RP が BE / BS flags の最新値を user account とともに保存することを **RECOMMENDED** としています（§6.1.3）。

ここで BE と BS の性質は異なります。BE は credential 作成後に変化しない値ですが、BS は後の authentication ceremony で変化し得ます。

## 5. authentication で RP が検証すること

§7.2 の authentication assertion verification では、まず BE / BS の不正な組み合わせを検出します。

RP は BE bit が set されていない場合、BS bit も set されていないことを検証します（§7.2 step 18）。これは §6.1.3 の `BE=0, BS=1` が許可されないという定義に対応します。

credential backup state を RP の business logic または policy の一部として使う場合、§7.2 step 19 は現在の BE / BS と credential record の値を比較する処理を定義しています。

1. `currentBe` と `currentBs` を今回の `authData.flags` から取得する。
2. 保存済み `credentialRecord.backupEligible` が set なら、`currentBe` が set であることを検証する。
3. 保存済み `credentialRecord.backupEligible` が set でなければ、`currentBe` が set されていないことを検証する。
4. RP policy があれば適用する。

BE は変更不可の credential property なので、authentication 時の BE と保存済み `backupEligible` の一致を確認できます。BS は現在状態なので、値が変化し得ます。

<pre class="mermaid">
flowchart TD
    A[Assertion を受信] --> B[authData.flags を読む]
    B --> C{BE=0 か}
    C -->|Yes| D[BS=0 を検証]
    C -->|No| E[BE=1]
    D --> F[保存済み backupEligible と比較]
    E --> F
    F --> G[必要なら RP policy を適用]
</pre>

## 6. BS の変化を仕様はどう扱うか

§6.1.3 では BS が時間とともに変化し得ることを明記しています。`BE=1, BS=0` と `BE=1, BS=1` は、同じ multi-device credential が異なる時点で取り得る状態です。

仕様は RP に対する利用例も示していますが、§7.2 step 19 で実際に適用する business logic / policy は RP policy に委ねています。本記事では、どの policy を選ぶべきかは扱いません。

**The specification defines the signal and validation rules; RP policy determines how the signal affects application behavior.**  
（仕様は signal と検証規則を定義し、その signal をアプリケーション動作にどう反映するかは RP policy が決定します。）

## 7. Article brief

- **Reader:** WebAuthn response verification と credential record を実装・レビューする RP 担当者。
- **Question:** BE / BS flags は何を表し、どの値が変化し得て、RP は registration / authentication で何を確認するのか。
- **Answer:** BE は変更されない backup eligibility、BS は変化し得る現在の backup state であり、有効な組み合わせと §7.1 / §7.2 の処理を区別して理解できる。
- **Scope:** WebAuthn Level 3 の BE / BS flags、credential backup eligibility / state、RP verification。
- **Out of scope:** backup / sync mechanism、account recovery、UP / UV、signature counter、attestation format。
- **Primary sources:** W3C Web Authentication Level 3 §4, §6.1, §6.1.3, §7.1, §7.2。
- **Diagram:** BE / BS の有効な組み合わせと authentication 時の検証を示す縦方向 flowchart。

## 8. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §4, §6.1, §6.1.3, §7.1, §7.2  
最終確認: 2026-09-22
