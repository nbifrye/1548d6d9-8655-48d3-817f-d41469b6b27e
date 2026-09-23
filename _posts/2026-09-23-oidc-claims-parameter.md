---
layout: post
title: "OpenID Connect Core：claims parameter で個別の Claim をどう要求するのか"
date: 2026-09-23 15:46:00 +0900
categories: [authentication, oidc]
---

OpenID Connect Core 1.0 incorporating errata set 2 は、Authentication Request の `claims` parameter を使って、ID Token と UserInfo Response に含める個別の Claim を要求する方法を §5.5 と §5.5.1 に定義しています。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** OpenID Connect の Relying Party（RP）で、scope value より細かい単位で Claim を要求する実装者・レビュー担当者  
**この記事で伝えること:** `claims` parameter の配置、`userinfo` / `id_token` の構造、個別 Claim の `null` / `essential` / `value` / `values` の意味と処理を確認する  
**扱わないこと:** scope value による Claim set の詳細、Claim の言語タグ、Request Object の署名・暗号化、個別仕様が追加する Claim、UserInfo Endpoint の呼び出し手順、ID Token 全体の検証手順

## Article brief

- **Reader:** scope value より細かい単位で Claim を要求する OpenID Connect RP の実装者・レビュー担当者
- **Question:** `claims` parameter は Authorization Request のどこに置き、ID Token と UserInfo Response の Claim をどの JSON 構造で指定するのか。`essential`、`value`、`values` は何を意味するのか
- **Answer:** `claims` は Authentication Request parameter であり、その値は JSON object である。`userinfo` と `id_token` の各 member の下に個別 Claim を指定し、`null` または Claim 要求を修飾する JSON object を値として使用する
- **Scope:** OpenID Connect Core 1.0 incorporating errata set 2 §5.5、§5.5.1、および Authorization Request の serialization に必要な §3.1.2.1、§13.1–§13.2
- **Out of scope:** scope value の Claim set の詳細、Request Object、追加仕様固有の Claim、UserInfo Endpoint の取得処理、ID Token validation
- **Primary sources:** OpenID Connect Core 1.0 incorporating errata set 2 §3.1.2.1、§5.5、§5.5.1、§13.1–§13.2
- **Diagram:** RP が `claims` を含む Authentication Request を送り、OP が要求を `id_token` と `userinfo` の対象に分けて処理する関係を `flowchart TD` で示す

## 1. `claims` は Authentication Request parameter

OpenID Connect Core §5.5 は `claims` を、RP が個別の Claim を要求するための OPTIONAL parameter として定義しています。値は JSON object です。

Authorization Code Flow の Authentication Request を HTTP `GET` で送る場合、request parameter は §3.1.2.1 と §13.1 に従って URI query component に serialize されます。HTTP `POST` を使う場合は §13.2 の Form Serialization を使用します。

したがって、`claims` の JSON object を HTTP request body の JSON member として送るわけではありません。GET では query parameter の値、POST では form parameter の値です。

## 2. `claims` object は `userinfo` と `id_token` を分ける

§5.5 では `claims` object に次の member を定義しています。

- `userinfo`: UserInfo Response で要求する個別 Claim を表す JSON object。OPTIONAL
- `id_token`: ID Token で要求する個別 Claim を表す JSON object。OPTIONAL

どちらの member でも、さらに Claim name を member name として指定します。

構造は次のようになります。

```json
{
  "userinfo": {
    "email": null
  },
  "id_token": {
    "auth_time": {
      "essential": true
    }
  }
}
```

この JSON は非規範的な例です。`email` や `auth_time` の選択自体に推奨の意味はありません。

## 3. 個別 Claim の値は `null` または JSON object

OpenID Connect Core §5.5.1 により、`userinfo` と `id_token` の各 Claim member の値は、`null` または JSON object のいずれかでなければなりません（MUST）。

`null` は、その Claim を default manner で要求することを表します。この場合、その Claim は Voluntary Claim です。

JSON object を使う場合、Core は `essential`、`value`、`values` を定義しています。

### `essential`

`essential` は OPTIONAL の boolean です。`true` は Essential Claim、`false` は Voluntary Claim を表し、default は `false` です。

ただし §5.5.1 は、Essential Claim が返せない場合でも、個別 Claim の定義に別の規定がない限り、Authorization Server が Claim を返さなかったことだけを理由に error を生成してはならない（MUST NOT）としています。

### `value`

`value` は OPTIONAL で、特定の Claim value を要求します。指定値は対象 Claim に対して有効な値でなければなりません（MUST）。一致判定には equality comparison を使用します。

要求値と一致しない場合、その Claim は response に含まれません。ただし `sub` を特定値で要求した場合は例外で、不一致は §3.1.2.2 に従って authentication failure になります（MUST）。

### `values`

`values` は OPTIONAL で、許容する複数の Claim value を preference order で指定します。array 内の値は対象 Claim に対して有効でなければなりません（MUST）。処理は `value` と同様ですが、候補が複数あります。

どの要求値とも一致しない場合、その Claim は response に含まれません。

## 4. 非規範的な Authentication Request 例

次は、`email` を UserInfo Response に、`auth_time` を Essential Claim として ID Token に要求する例です。値は説明用です。

読みやすさのため、`claims` の値だけを percent-encoding 前の JSON として先に示します。

```json
{
  "userinfo": {
    "email": null
  },
  "id_token": {
    "auth_time": {
      "essential": true
    }
  }
}
```

HTTP `GET` では、この JSON object を JSON text として表現し、§13.1 の URI Query String Serialization に従って `claims` query parameter の値として encode します。

```http
GET /authorize?response_type=code&client_id=illustrative-client&scope=openid&redirect_uri=https%3A%2F%2Fclient.example%2Fcb&claims=%7B%22userinfo%22%3A%7B%22email%22%3Anull%7D%2C%22id_token%22%3A%7B%22auth_time%22%3A%7B%22essential%22%3Atrue%7D%7D%7D HTTP/1.1
Host: server.example
```

この HTTP request は非規範的な具体例です。`illustrative-client`、host、redirect URI は説明用の値であり、特定 deployment の設定を示しません。

## 5. `essential: true` は「返せなければ常に error」ではない

`essential: true` は、その Claim が RP にとって Essential Claim であることを表します。しかし Core §5.5.1 の一般則では、Claim が利用できない、または End-User が release を許可しなかったために返されない場合でも、Authorization Server は、それだけを理由に error を生成してはなりません（MUST NOT）。

個別 Claim の定義が別の処理を定める場合は、その規定が適用されます。たとえば §5.5.1.1 は、`acr` を Essential Claim とし、`value` または `values` で特定値を要求する場合について追加要件を定めていますが、その詳細は本稿の対象外です。

## 6. 処理関係

<pre class="mermaid">
flowchart TD
    A[RP] --> B[Authentication Request]
    B --> C[claims parameter]
    C --> D[userinfo member]
    C --> E[id_token member]
    D --> F[個別 Claim request]
    E --> G[個別 Claim request]
    F --> H[OP が要求を処理]
    G --> H
</pre>

この図は §5.5 のデータ構造と処理主体の関係を簡略化したものです。仕様にない actor や security property は追加していません。

## 7. まとめ

OpenID Connect Core の `claims` parameter は、RP が ID Token と UserInfo Response に対して個別の Claim を要求するための Authentication Request parameter です。

- `claims` の値は JSON object
- GET の場合は query parameter、POST の場合は form parameter として配置する
- `userinfo` と `id_token` の下で個別 Claim を指定する
- 個別 Claim の値は `null` または JSON object でなければならない（MUST、§5.5.1）
- `essential` は Essential / Voluntary を表す
- `value` は単一の要求値、`values` は preference order を持つ複数の要求値を表す
- 一般則では Essential Claim が返らないことだけを理由に error を生成してはならない（MUST NOT、§5.5.1）

## 参考仕様

- OpenID Foundation, **OpenID Connect Core 1.0 incorporating errata set 2**, §3.1.2.1, §5.5, §5.5.1, §13.1–§13.2  
  https://openid.net/specs/openid-connect-core-1_0.html
