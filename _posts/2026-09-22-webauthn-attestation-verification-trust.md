---
layout: post
title: "WebAuthn attestation の検証：fmt / attStmt / trust anchor / trustworthiness"
date: 2026-09-22 20:41:00 +0900
categories: [authentication, webauthn]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** WebAuthn registration で attestation statement の検証と trustworthiness assessment を実装・レビューする Relying Party（RP）の担当者  
**この記事で伝えること:** registration における `fmt` の識別、`attStmt` の暗号学的検証、acceptable trust anchor の取得、attestation trustworthiness の評価という §7.1 steps 21–24 の処理  
**扱わないこと:** `attestation` conveyance preference、個別 attestation statement format の内部アルゴリズム、trust anchor の具体的な選定方針、FIDO Metadata Service の利用方法、authentication ceremony

WebAuthn Level 3 の registration では、attestation statement の暗号学的な検証と、その statement を RP が信頼できるかという評価は別の処理です。本記事は W3C Web Authentication Level 3 §6.5、§6.5.2、§6.5.3、§6.5.4、§7.1 に範囲を限定します。

**Cryptographic validity and attestation trustworthiness are separate checks.**  
（暗号学的に有効であることと、attestation を信頼できることは別の検証です。）

## 1. 入力は attestation object の fmt / authData / attStmt

§7.1 step 13 では、RP は `AuthenticatorAttestationResponse.attestationObject` を CBOR decode し、`fmt`、`authData`、`attStmt` を取得します。§6.5.4 で attestation object は CBOR map として定義されています。

次は配置と構造だけを示す非規範的な最小例です。値は illustrative value であり、特定の authenticator や trust property を表しません。

```text
{
  authData: <bytes>,
  fmt: "packed",
  attStmt: {
    alg: -7,
    sig: <bytes>,
    x5c: [<certificate bytes>]
  }
}
```

- `fmt`: text。attestation statement format identifier。
- `authData`: bytes。authenticator data。
- `attStmt`: map または array。具体的な構造は `fmt` に対応する attestation statement format が定義する。
- 配置: `fmt`、`authData`、`attStmt` は JSON member ではなく、CBOR encoded `response.attestationObject` を decode して得る attestation object の要素。

この例の `packed` 構造は §8.2 の形式を最小限に示したものです。本記事では packed format 固有の verification procedure は扱いません。

## 2. step 21：fmt から statement format を決定する

§7.1 step 21 では、RP は `fmt` を、サポートする WebAuthn Attestation Statement Format Identifier の集合に対して USASCII case-sensitive match し、attestation statement format を決定します。

§8.1 は attestation statement format identifier の照合を case-sensitive に行わなければならないと定めています（**MUST**, §8.1）。

`fmt` は statement の syntax と verification procedure を選ぶための識別子です。§6.5 は attestation statement format と attestation type を区別しています。format は statement の表現方法と contextual binding の組み込み方を定め、attestation type は underlying trust model の semantics を定めます。

## 3. step 22：fmt 固有の verification procedure を実行する

§7.1 step 22 では、RP は `fmt` に対応する verification procedure に `attStmt`、`authData`、`hash` を渡し、`attStmt` が valid attestation signature を convey する正しい attestation statement であることを検証します。

ここで `hash` は §7.1 step 12 で `response.clientDataJSON` に SHA-256 を適用した結果です。

**The verification procedure is selected by `fmt`; WebAuthn does not define one format-independent signature check for every attestation statement.**  
（verification procedure は `fmt` によって選ばれ、すべての attestation statement に共通する単一の署名検証手順があるわけではありません。）

各 format の verification procedure は §8 で個別に定義されています。本記事では、その内部手順を横断的に混在させません。

## 4. step 23：acceptable trust anchor を取得する

step 22 の validation が成功した場合、§7.1 step 23 では、RP はその attestation type と `fmt` に対する acceptable trust anchors、すなわち attestation root certificates の list を trusted source または policy から取得します。

仕様は FIDO Metadata Service を取得方法の一例として挙げていますが、acceptable trust anchor をどの source や policy から選ぶかを一意には定めていません。本記事でも特定の source や policy を推奨しません。

§7.1 はさらに、attestation object を検証する RP には acceptable trust anchors を決定する trusted method が必要であるとしています。certificate を使用する場合、RP は intermediate CA certificate の status information にアクセスできなければならず（**MUST**）、client が chain を提供しなかった場合には attestation certificate chain を構築できなければなりません（**MUST**, §7.1）。

## 5. step 24：cryptographic validity の後で trustworthiness を評価する

§7.1 step 24 は、step 22 の verification procedure の出力を使って attestation trustworthiness を評価します。

1. no attestation の場合、RP policy で None attestation が acceptable かを検証する。
2. self attestation の場合、RP policy で self attestation が acceptable かを検証する。
3. それ以外では、verification procedure が返した X.509 certificate の attestation trust path を使い、attestation public key が acceptable root certificate まで正しく chain するか、またはその key の certificate 自体が acceptable certificate であることを検証する。

attestation statement が trustworthy と判断されない場合、RP は registration ceremony を失敗させることが **SHOULD** です（§7.1）。一方、policy が許す場合、RP は credential ID と credential public key を登録しつつ、その credential を self attestation と同様に扱うことができます（**MAY**, §7.1）。その場合、特定の authenticator model が credential を生成したという cryptographic proof はないものとして扱われます。

仕様がこの判断を RP policy に委ねているため、本記事では fail と accept のどちらかを推奨しません。

<pre class="mermaid">
flowchart TD
    A[CBOR decode] --> B[fmt を識別]
    B --> C[fmt 固有の検証]
    C --> D[trust anchor を取得]
    D --> E[trustworthiness を評価]
    E --> F[RP policy に従う]
</pre>

この図は §7.1 steps 13、21–24 の関係を示す非規範的な要約です。個別 format の内部処理や、仕様にない trust source は追加していません。

## 6. format と type を混同しない

§6.5 は、attestation statement format が syntax を、attestation type が trust model を定めると説明しています。両者には一般に単純な一対一対応はありません。たとえば `packed` format は複数の attestation type と組み合わせられます。

したがって §7.1 の処理は、`fmt` を識別して statement を cryptographically validate する段階と、その結果および trust anchor を使って trustworthiness を評価する段階に分かれています。

## 7. Article brief

- **Reader:** WebAuthn registration で attestation statement の検証と trustworthiness assessment を実装・レビューする RP 担当者。
- **Question:** `attestationObject` を decode した後、RP は `fmt`、`attStmt`、trust anchor をどの順序で扱い、暗号学的な validity と trustworthiness をどう区別するのか。
- **Answer:** §7.1 steps 21–24 に沿って、format identification、format-specific verification、acceptable trust anchor の取得、trustworthiness assessment を区別して理解できる。
- **Scope:** attestation object の最小構造、§6.5 の format / type の区別、§7.1 steps 21–24 の RP processing。
- **Out of scope:** conveyance preference、各 format の内部 verification algorithm、trust anchor の具体的な選定方針、FIDO Metadata Service の利用方法、authentication ceremony。
- **Primary sources:** W3C Web Authentication Level 3 §6.5, §6.5.2, §6.5.3, §6.5.4, §7.1, §8.1。
- **Diagram:** attestation object の decode から format identification、format-specific verification、trust anchor acquisition、trustworthiness assessment までの縦方向 flowchart。

## 8. 一次資料

- W3C Recommendation: [Web Authentication: An API for accessing Public Key Credentials - Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/)

参照した主要節: §6.5, §6.5.2, §6.5.3, §6.5.4, §7.1, §8.1  
最終確認: 2026-09-22
