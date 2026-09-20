---
layout: post
title: "WebAuthn Level 3：related origins は RP ID の利用範囲をどう扱うのか"
date: 2026-09-20 10:40:00 +0900
categories: [authentication, webauthn]
---

<!--
Article brief
Reader: 複数の関連 origin で同じ RP ID を利用する WebAuthn RP 実装者
Question: 通常の RP ID の範囲外にある関連 origin から、同じ RP ID を使う要求はどのように検証されるのか
Answer: RP が共通 RP ID と /.well-known/webauthn の origins を用意し、対応 Client が related origins validation procedure に従って caller origin を検証する処理を説明できる
Scope: WebAuthn Level 3 §5.11, §5.11.1、および create/get における RP ID validation との接続
Out of scope: credential registration/assertion の RP 側検証全般、iframe、conditional mediation、deployment 上の origin 選定
Primary sources: W3C Web Authentication Level 3 Recommendation §5.11, §5.11.1, §5.1.3, §5.1.4
Diagram: related origins validation procedure の flowchart
-->

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** 複数の関連 origin で同じ RP ID を利用する WebAuthn RP 実装者  
**この記事で伝えること:** 通常の RP ID の範囲外にある origin から共通 RP ID を指定したとき、WebAuthn Client が `/.well-known/webauthn` を使って related origin を検証する仕組み  
**扱わないこと:** credential registration / assertion の RP 側検証全般、cross-origin `iframe`、conditional mediation、どの origin を関連付けるべきかという deployment 判断

WebAuthn Level 3 §5.11 は **related origin requests** を定義しています。通常、RP ID は origin の effective domain と同一、またはその registrable domain suffix である必要があります。related origin requests を利用すると、Relying Party は限定された関連 origin の集合から、共通の RP ID を使って credential を作成・利用できるように構成できます。

この機能を利用する Relying Party は、関連するすべての origin の ceremony で共通の RP ID を選択しなければなりません（**MUST**, §5.11）。

## 1. 通常の RP ID validation との違い

`navigator.credentials.create()` と `navigator.credentials.get()` の処理では、指定された RP ID が caller origin の effective domain と同一または registrable domain suffix であれば、通常の RP ID validation の範囲内です。

その条件を満たさない RP ID が指定された場合、Client が related origin requests をサポートしていれば、Client は **related origins validation procedure** を実行します。検証結果が `false` の場合は `SecurityError` を送出します（§5.1.3、§5.1.4）。Client がこの機能をサポートしていない場合も `SecurityError` になります。

つまり related origins は RP ID 自体を origin ごとに変更する仕組みではありません。複数の関連 origin から **同じ RP ID** を要求できるようにし、その origin が RP ID 側で公開された一覧に含まれるかを Client が確認します。

## 2. RP ID 側の `/.well-known/webauthn`

RP は RP ID の `webauthn` well-known URL に JSON document を配置します（**MUST**, §5.11）。URL は次の形です。

```text
https://{RP-ID}/.well-known/webauthn
```

この document は HTTPS で提供しなければなりません（**MUST**）。response の Content-Type は `application/json` でなければならず（**MUST**）、top-level JSON object は `origins` key を含まなければなりません（**MUST**）。`origins` の値は1個以上の web origin string を含む array です（**MUST**, §5.11）。

次は形式と配置を示す**非規範的な例**です。値は illustrative value です。

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

- `origins`: top-level JSON member。値は1個以上の string からなる array。
- 各 string: web origin。

## 3. Client は related origin をどう検証するか

WebAuthn Level 3 §5.11.1 の related origins validation procedure は、`callerOrigin` と要求された `rpIdRequested` を入力として処理します。

<pre class="mermaid">
flowchart TD
    A[callerOrigin と rpIdRequested] --> B[RP ID の well-known URL を取得]
    B --> C{200 / JSON / origins array?}
    C -- No --> D[SecurityError]
    C -- Yes --> E[origins を順に確認]
    E --> F{callerOrigin と same origin?}
    F -- Yes --> G[true]
    F -- No --> H{確認対象が残る?}
    H -- Yes --> E
    H -- No --> I[false]
</pre>

Client は `https://{rpIdRequested}/.well-known/webauthn` を取得します。fetch は credentials と referrer を付けず、`https:` scheme を使用します。redirect をたどる場合も、すべての redirect に `https:` を明示的に要求しなければなりません（**MUST**, §5.11）。

§5.11.1 では、fetch failure、最終 status code が `200` でない場合、Content-Type が `application/json` でない場合、body が valid JSON object でない場合、または `origins` が存在しない・string array でない場合に `SecurityError` を送出します。

有効な `origins` array が得られると、Client は各 item を URL として処理し、Client policy が許容する registrable origin label 数の範囲で `callerOrigin` と same origin である item を探します。一致すれば procedure は `true`、最後まで一致しなければ `false` を返します（§5.11.1）。

## 4. Client policy が決める上限

related origins をサポートする Client は、少なくとも5個の **registrable origin labels** をサポートしなければなりません（**MUST**, §5.11）。また Client policy は abuse を防ぐための上限を定義することが推奨されています（**SHOULD**, §5.11）。

この上限は `origins` array の単純な要素数と同義ではありません。§5.11.1 の algorithm は各 origin の effective domain から registrable origin label を求め、`labelsSeen` と Client policy の `maxLabels` を使って処理対象を制御します。具体的な `maxLabels` の値は Client policy に委ねられており、本記事では特定の値を推奨しません。

## 5. `create()` と `get()` のどこで使われるか

credential creation では `PublicKeyCredentialCreationOptions.rp.id`、authentication では `PublicKeyCredentialRequestOptions.rpId` が RP ID の入力になります。

指定された RP ID が caller origin の通常の RP ID 条件を満たさない場合に限り、対応 Client は related origins validation procedure を呼び出します。したがって `/.well-known/webauthn` は credential data を格納する endpoint ではなく、**caller origin が要求された RP ID の related origin として列挙されているかを Client が検証するための document** です。

Client が feature discovery を提供する場合、related origin requests をサポートする Client は `getClientCapabilities()` の response に `relatedOrigins` を含めることが推奨されています（**SHOULD**, §5.11）。

## 6. RP 側の origin 検証とは別の処理

related origins validation procedure は Client が RP ID の利用可否を判断する処理です。これによって、RP が registration または authentication response の `clientDataJSON` に含まれる origin を検証する処理が不要になるわけではありません。

WebAuthn Level 3 の RP operation では、RP は response の origin がその RP に期待される origin であることを検証します。§7 の検証手順全体は本記事の scope 外です。

## まとめ

Related origin requests は、通常の RP ID の domain 関係を満たさない複数の関連 origin から、共通の RP ID を利用するための WebAuthn Level 3 の仕組みです。RP は共通 RP ID を使用し、その RP ID の `/.well-known/webauthn` に許可する web origins を JSON array として公開します。Client は RP ID validation の際にこの document を HTTPS で取得し、§5.11.1 の procedure に従って caller origin を照合します。

## 一次資料

- W3C, *Web Authentication: An API for accessing Public Key Credentials — Level 3*, §5.1.3, §5.1.4, §5.11, §5.11.1  
  <https://www.w3.org/TR/webauthn-3/>
