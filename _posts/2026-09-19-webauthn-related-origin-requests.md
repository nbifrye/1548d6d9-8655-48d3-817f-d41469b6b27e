---
layout: post
title: "WebAuthn Level 3：Related Origin Requests では異なる origin から同じ RP ID をどう検証するのか"
date: 2026-09-19 21:43:00 +0900
categories: [authentication, webauthn]
---

WebAuthn では通常、RP ID は呼び出し元 origin の effective domain と同じか、その registrable domain suffix である必要があります。WebAuthn Level 3 の Related Origin Requests は、RP が明示的に opt in することで、異なる registrable domain の origin から共通の RP ID を使用するための検証手順を定義しています。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** 複数の関連 domain で同じ RP ID を使う WebAuthn RP / Web frontend の実装・レビュー担当者  
**この記事で伝えること:** Related Origin Requests で RP が公開する `/.well-known/webauthn` の JSON 構造と、WebAuthn Client が caller origin を検証する処理  
**扱わないこと:** cross-origin iframe、passkey の同期、registration / authentication ceremony 全般、attestation、ブラウザごとの実装状況、関連 domain を採用するかどうかの判断

## Article brief

- **Reader:** 複数の関連 domain で同じ RP ID を使う WebAuthn RP / Web frontend の実装・レビュー担当者
- **Question:** 呼び出し元 origin が RP ID の registrable domain suffix 関係にない場合、Related Origin Requests では何を公開し、Client はどのようにその origin を検証するのか
- **Answer:** RP が共通 RP ID を使い、その RP ID の `/.well-known/webauthn` に `origins` 配列を持つ JSON document を HTTPS で公開し、Client がその document を取得して caller origin を検証する流れを追える
- **Scope:** WebAuthn Level 3 §5.11、§5.11.1、関連する §5.1.3 / §5.1.4 の RP ID validation、および §5.8.7 の `relatedOrigins` capability
- **Out of scope:** cross-origin iframe と Permissions Policy、ceremony 全般、attestation、credential sync、実装製品ごとの対応状況、deployment の推奨
- **Primary sources:** W3C Web Authentication: An API for accessing Public Key Credentials Level 3 §5.11、§5.11.1、§5.1.3、§5.1.4、§5.8.7、§12.5
- **Diagram:** caller origin、WebAuthn Client、RP ID の `/.well-known/webauthn` の間で行われる validation を示す縦方向 flowchart

## 1. 通常の RP ID validation と Related Origin Requests

WebAuthn Level 3 §5.11 では、通常、RP ID は origin の effective domain と同じか、その registrable domain suffix である必要があります。

たとえば caller origin が `https://login.example.com` なら、`example.com` は通常の RP ID validation の範囲に入ります。一方、caller origin が `https://example.co.uk` で RP ID に `example.com` を指定する場合、この suffix 関係だけでは validation を通過しません。

Related Origin Requests を利用する RP は、関連 origin のすべての ceremony で共通の RP ID を選択しなければなりません（MUST、§5.11）。そのうえで、RP ID 側に関連 origin の一覧を公開します。

この仕組みは、credential の RP ID 自体を origin ごとに変更するものではありません。Authenticator data の `rpIdHash` は RP ID の SHA-256 hash であり、Authenticator は assertion 生成時に credential が scope されている RP ID と Client から渡された RP ID が一致することを検証します（§6.1）。

## 2. RP ID 側に `/.well-known/webauthn` を公開する

WebAuthn Level 3 §5.11 は、RP ID の `webauthn` well-known URL に JSON document を置くことを MUST としています。§12.5 は `webauthn` を well-known URI suffix として登録しています。

RP ID が `example.com` の場合、取得先は次の位置です。

```text
https://example.com/.well-known/webauthn
```

document は HTTPS で提供しなければならず（MUST）、response の Content-Type は `application/json` でなければなりません（MUST）。top-level JSON object は `origins` key を持ち、その値は1個以上の web origin string からなる array でなければなりません（MUST、§5.11）。

次は構造を確認するための**非規範的な例**です。domain 名は illustrative value です。

```http
GET /.well-known/webauthn HTTP/1.1
Host: example.com
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "origins": [
    "https://example.co.uk",
    "https://example.sg"
  ]
}
```

`origins` は JSON member であり、HTTP header や WebAuthn API の option member ではありません。

- **`origins`:** array of strings。1個以上の web origin を含む（§5.11）。
- **配置:** RP ID の `/.well-known/webauthn` が返す top-level JSON object。
- **取得方法:** HTTPS。Client は credentials と referrer を付けずに取得する（§5.11）。

## 3. Client は caller origin をどう検証するか

WebAuthn Level 3 §5.11.1 の related origins validation procedure は、`callerOrigin` と要求された RP ID `rpIdRequested` を入力として処理します。

<pre class="mermaid">
flowchart TD
    A[caller origin が WebAuthn を呼ぶ] --> B[RP ID を指定]
    B --> C{通常の RP ID validation を満たすか}
    C -->|yes| D[通常どおり処理を続行]
    C -->|no| E[Related Origin Requests を確認]
    E --> F[RP ID の /.well-known/webauthn を取得]
    F --> G[status / Content-Type / JSON を検証]
    G --> H[origins を順に評価]
    H --> I{caller origin と same origin か}
    I -->|yes| D
    I -->|no| J[validation failure]
</pre>

Client は `https://<rpIdRequested>/.well-known/webauthn` を credentials なし、referrer なしで取得します（§5.11.1）。fetch が失敗する、最終 response が HTTP 200 でない、Content-Type が `application/json` でない、body が valid JSON object でない、または `origins` が string array でない場合は `SecurityError` になります。

その後 Client は `origins` の各値を URL として処理し、caller origin と same origin の entry が見つかれば validation procedure は `true` を返します。見つからなければ `false` を返します（§5.11.1）。

**The authorization is anchored at the requested RP ID's well-known resource, not at the caller origin.**  
（この検証は caller origin 側ではなく、要求された RP ID 側の well-known resource を基点に行われます。）

## 4. registrable origin label には Client policy による上限がある

§5.11.1 の validation procedure は、Client policy が許容する registrable origin label の最大数を `maxLabels` として扱います。`origins` を上から処理し、すでに `maxLabels` 個の異なる registrable origin label を処理した後に新しい label が現れた場合、その entry は skip されます。

WebAuthn Level 3 §5.11 は、この feature をサポートする Client が少なくとも5個の registrable origin labels をサポートしなければならない（MUST）と定めています。一方、abuse を防ぐための上限は Client policy が定義することを SHOULD としています。

したがって、仕様はすべての Client に同一の最大値を要求していません。この記事では特定の上限値を推奨しません。

## 5. WebAuthn API から指定する RP ID の位置

Related Origin Requests 専用の request parameter が追加されるわけではありません。registration では `PublicKeyCredentialCreationOptions.rp.id`、authentication では `PublicKeyCredentialRequestOptions.rpId` として、通常の WebAuthn option に共通 RP ID を指定します。

次は配置を示すための**非規範的な最小例**です。値は illustrative value です。

```javascript
const publicKey = {
  challenge: challengeBytes,
  rpId: "example.com"
};

await navigator.credentials.get({ publicKey });
```

caller origin が `https://example.co.uk` で、`example.com` が通常の suffix validation を満たさない場合、Related Origin Requests をサポートする Client は §5.1.4 の処理から §5.11.1 の validation procedure を実行します。validation が失敗した場合は `SecurityError` になります。

registration でも対応する処理が §5.1.3 に定義されており、指定位置は `publicKey.rp.id` です。

## 6. feature support は `relatedOrigins` capability で表される

WebAuthn Level 3 §5.8.7 は Client capability `relatedOrigins` を定義しています。この値は、WebAuthn Client が Related Origin Requests をサポートすることを表します。

また §5.11 は、この feature をサポートする Client が `getClientCapabilities()` の response に `relatedOrigins` を含めることを SHOULD としています。

この capability は `/.well-known/webauthn` の `origins` member とは別のデータです。前者は Client の feature capability、後者は RP ID が公開する related origin の一覧です。

## 7. 仕様上の境界

Related Origin Requests は、任意の origin が任意の RP ID を使える仕組みではありません。RP ID 側の well-known resource に caller origin が現れ、Client の validation procedure を通過する必要があります。

また、cross-origin `iframe` で WebAuthn API を利用するための Permissions Policy は §5.10 の別機構です。Related Origin Requests は、異なる registrable domain の origin と共通 RP ID の関係を検証する §5.11 の機構であり、この記事では両者を混在させません。

## Primary sources

- W3C, *Web Authentication: An API for accessing Public Key Credentials Level 3*, §5.1.3, §5.1.4, §5.8.7, §5.11, §5.11.1, §6.1, §12.5  
  <https://www.w3.org/TR/webauthn-3/>
