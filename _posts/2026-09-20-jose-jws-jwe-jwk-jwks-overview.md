---
layout: post
title: "JOSE：JWS / JWE / JWK / JWK Set はそれぞれ何を担うのか"
date: 2026-09-20 00:40:00 +0900
categories: [jose, jwt]
---

## この記事について

**記事タイプ:** Overview  
**対象読者:** JOSE を初めて扱い、JWS / JWE / JWK / JWK Set の役割とデータ構造の違いを整理したい実装者  
**この記事で伝えること:** JWS は署名または MAC による integrity protection、JWE は暗号化と integrity protection、JWK は暗号鍵の JSON 表現、JWK Set は複数 JWK の JSON 表現を担い、JWA がそれらで使う暗号アルゴリズムと識別子を定義すること  
**扱わないこと:** JWT の claim validation、OAuth / OpenID Connect 固有の利用規則、鍵配布 endpoint、鍵ローテーション手順、個別アルゴリズムの選定、暗号処理の実装手順

## Article brief

- **Reader:** JOSE を初めて扱う実装者
- **Question:** JWS / JWE / JWK / JWK Set は何が違い、どのデータが message で、どのデータが key なのか
- **Answer:** JWS と JWE は保護された message の表現、JWK と JWK Set は cryptographic key の表現であり、JWA はそれらで使う algorithm identifier と algorithm-specific semantics を定義する
- **Scope:** RFC 7515 §1–§3・§7、RFC 7516 §1–§3・§7、RFC 7517 §1–§5、RFC 7518 §1 の役割と代表的な構造
- **Out of scope:** application profile、JWT claim、algorithm selection、key distribution、key rotation、X.509 との運用比較
- **Primary sources:** RFC 7515、RFC 7516、RFC 7517、RFC 7518
- **Diagram:** message protection と key representation の関係を示す `flowchart TD`

## 1. JOSE の仕様は message と key を別のデータ構造として定義する

RFC 7515 §1 では、JWS は JSON-based data structures を使って、digital signature または MAC により content を保護する形式として定義されています。JWS の cryptographic mechanisms は任意の octet sequence に integrity protection を提供します。

RFC 7516 §1 では、JWE は encrypted content の JSON-based representation として定義されています。JWE の cryptographic mechanisms は任意の octet sequence を暗号化し、integrity protection を提供します。

RFC 7517 §1 は JWK を cryptographic key を表す JSON data structure と定義し、複数の JWK を表す JWK Set も定義しています。

RFC 7518 §1 は、JWS、JWE、JWK で使う cryptographic algorithms と identifiers、および algorithm-specific semantics / operations を定義します。

<pre class="mermaid">
flowchart TD
    A[保護する content]
    A --> B[JWS]
    A --> C[JWE]
    D[JWK]
    D --> B
    D --> C
    E[JWK Set]
    E --> D
    F[JWA]
    F --> B
    F --> C
    F --> D
</pre>

この図は仕様間の役割を示す非規範的な整理です。特定の application がどの key をどのように取得・選択するかは、ここでは定めていません。

## 2. JWS は content の integrity を保護する

RFC 7515 §3 では、JWS は次の論理値を表します。

- **JOSE Header:** signature / MAC 処理に関する Header Parameter
- **JWS Payload:** 保護対象の octet sequence
- **JWS Signature:** JWS Protected Header と JWS Payload に対する digital signature または MAC

RFC 7515 §7.1 の JWS Compact Serialization は、3つの base64url-encoded 部分を `.` で連結します。

次は配置を示すための非規範的な構造例です。各値は illustrative value であり、有効な署名値ではありません。

```text
BASE64URL(PROTECTED_HEADER).
BASE64URL(PAYLOAD).
BASE64URL(SIGNATURE)
```

実際の serialization では改行せず1つの string です。RFC 7515 §7.1 では、順序は `JWS Protected Header`、`JWS Payload`、`JWS Signature` です。

JWS JSON Serialization も RFC 7515 §7.2 で定義されています。Compact Serialization と JSON Serialization の選択は application が指定します。

## 3. JWE は content を暗号化し integrity も保護する

RFC 7516 §2–§3 では、JWE は encrypted and integrity-protected message を表します。JWE は JOSE Header、JWE Encrypted Key、JWE Initialization Vector、JWE AAD、JWE Ciphertext、JWE Authentication Tag という論理値を扱います。

RFC 7516 §7.1 の JWE Compact Serialization は5つの部分からなります。

次は配置を示すための非規範的な構造例です。値は illustrative value です。

```text
BASE64URL(PROTECTED_HEADER).
BASE64URL(ENCRYPTED_KEY).
BASE64URL(INITIALIZATION_VECTOR).
BASE64URL(CIPHERTEXT).
BASE64URL(AUTHENTICATION_TAG)
```

実際の serialization では改行せず1つの string です。RFC 7516 §3.1 / §7.1 の順序を示しています。

JWE JSON Serialization は RFC 7516 §7.2 で別に定義され、同じ content を複数 recipient 向けに暗号化する表現を可能にします。

## 4. JWK は cryptographic key を JSON object として表す

RFC 7517 §2 / §4 では、JWK は cryptographic key を表す JSON object です。object members が key の properties と value を表します。

`kty` は key type を識別する member で、JWK に存在しなければなりません（MUST, RFC 7517 §4.1）。key type 固有の members は RFC 7518 §6 などで定義されます。

次は RFC 7517 §3 と同じ EC key の構造を短く示した非規範的な例です。値は構造説明用です。

```json
{
  "kty": "EC",
  "crv": "P-256",
  "x": "illustrative-x-coordinate",
  "y": "illustrative-y-coordinate",
  "kid": "illustrative-key-id"
}
```

- **`kty`:** key type。MUST, RFC 7517 §4.1。
- **`kid`:** specific key を match するための case-sensitive string。OPTIONAL, §4.5。
- **`crv` / `x` / `y`:** EC key type 固有の members。RFC 7518 §6.2 が形式を定義します。

RFC 7517 §4.5 では、JWS / JWE とともに `kid` を使う場合、JWK の `kid` は JWS / JWE の `kid` Header Parameter と match するために使われます。

## 5. JWK Set は複数の JWK を `keys` array に入れる

RFC 7517 §2 / §5 では、JWK Set は JWK の集合を表す JSON object です。top-level の `keys` member は必須（MUST）で、その値は JWK の array です。

次は最小構造を示す非規範的な例です。key values は illustrative value です。

```json
{
  "keys": [
    {
      "kty": "EC",
      "crv": "P-256",
      "x": "illustrative-x-coordinate",
      "y": "illustrative-y-coordinate",
      "kid": "illustrative-key-id"
    }
  ]
}
```

JWK Set は key の集合を表す data structure です。この RFC 自体は、特定の OAuth / OpenID Connect endpoint から JWK Set を取得する手順を定義していません。

## 6. JWA は JWS / JWE / JWK で使う algorithm identifier を定義する

RFC 7518 §1 は JWS、JWE、JWK で使う cryptographic algorithms と identifiers を定義します。したがって、JWS / JWE は message representation、JWK / JWK Set は key representation、JWA はそれらで参照する algorithm definitions という役割分担になります。

個別 algorithm の現在の登録状態や、application profile がどの algorithm を要求・禁止するかは本記事の scope 外です。

## 7. 役割を読み分ける

JWS を見たときは「どの content に signature または MAC による integrity protection を与えているか」、JWE を見たときは「どの plaintext を encrypted and integrity-protected message として表しているか」を確認します。

JWK を見たときは message ではなく cryptographic key の JSON representation を見ています。JWK Set はその JWK を `keys` array にまとめる container です。

**JWS and JWE describe protected messages; JWK and JWK Set describe cryptographic keys.**  
（JWS と JWE は保護された message を表し、JWK と JWK Set は cryptographic key を表します。）

## 一次資料

- RFC 7515, *JSON Web Signature (JWS)*, §§1–3, 7
- RFC 7516, *JSON Web Encryption (JWE)*, §§1–3, 7
- RFC 7517, *JSON Web Key (JWK)*, §§1–5
- RFC 7518, *JSON Web Algorithms (JWA)*, §1, §6
