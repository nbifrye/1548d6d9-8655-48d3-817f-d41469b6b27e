---
layout: post
title: "RFC 8707：resource parameter は Access Token の対象 Resource をどう示すのか"
date: 2026-09-19 07:46:00 +0900
categories: [oauth]
tags: [OAuth, RFC8707, Resource Indicators]
---

**記事タイプ:** Feature Deep Dive  
**対象読者:** OAuth 2.0 の Authorization Request / Token Request と Access Token の対象 Resource の関係を実装・レビューする開発者  
**この記事で伝えること:** RFC 8707 の `resource` parameter が、Client が Access Token を使用する対象 Resource を Authorization Server にどう示すか  
**扱わないこと:** `scope` の一般的な設計、Token Exchange、Access Token の具体的な token format、Resource Server における token validation 手順

## Article brief

- **Reader:** OAuth 2.0 の Authorization Request / Token Request と Access Token の対象 Resource の関係を実装・レビューする開発者
- **Question:** Client は Access Token を使用する対象 Resource を Authorization Server にどのように伝え、Authorization Server はその情報をどう扱うのか
- **Answer:** `resource` parameter の値の制約、Authorization Request / Access Token Request での意味、複数 Resource、`invalid_target`、Access Token の audience restriction との関係を RFC 8707 に沿って説明できる
- **Scope:** RFC 8707 §2、§2.1、§2.2、§3
- **Out of scope:** Token Exchange、`scope` の一般論、JWT Access Token Profile、Token Introspection の処理手順、Resource Server の token validation
- **Primary sources:** RFC 8707
- **Diagram:** Client が `resource` を Authorization Server に送り、Authorization Server が対象 Resource を考慮して Access Token を発行する関係を縦方向の flowchart で示す

## 1. `resource` は Access Token の使用先を示す

RFC 8707 §2 は、Client がアクセスを要求する protected resource を Authorization Server に示すための `resource` request parameter を定義しています。Client は Authorization Server への request に `resource` parameter を含めることができます（MAY）。

`resource` の値は absolute URI でなければなりません（MUST）。fragment component を含めてはなりません（MUST NOT）。query component は含めるべきではありません（SHOULD NOT）が、application への request を query parameter で限定する場合など、query component が必要となる場合があることも RFC 8707 §2 は認めています。

`resource` URI は Resource の identity を表す identifier です。その URI は、対象 Resource が配置された network-addressable location に対応する locator である場合もあります（MAY）。

## 2. 複数の Resource も指定できる

RFC 8707 §2 では、複数の `resource` parameter を使用して、requested token を複数の Resource で使用する意図を示すことができます（MAY）。

例えば、SCIM API が `/Users`、`/Groups`、`/Schemas` など複数 endpoint を持つ場合について、RFC 8707 §2 はそれらを包含する Resource identifier の例として `https://apps.example.com/scim/` を示しています。

<pre class="mermaid">
flowchart TD
    A[Client] --> B[resource を含む request]
    B --> C[Authorization Server]
    C --> D[対象 Resource を評価]
    D --> E[Access Token を発行]
    E --> F[対象 Resource]
</pre>

この図は `resource` parameter が request から Access Token の対象 Resource の決定に関与する位置だけを示しています。Access Token の format や Resource Server 側の validation procedure は図に含めていません。

## 3. Authorization Request での `resource`

RFC 8707 §2.1 では、Authorization Request の `resource` parameter は、Client が access を要求する target service または protected resource を示します。

Authorization Server は、Authorization Request で示された Resource を authorization grant に関連付けます。その後の Authorization Code を使った Access Token Request では、Client が Token Request に `resource` を含めなかった場合、Authorization Server は Authorization Request で指定された Resource を使用して Access Token の対象を決定できます。

複数 Resource が Authorization Request に含まれていた場合、Authorization Server はそれらを authorization grant と関連付けることができます。どの Resource に対して token を発行するかは、後続の Access Token Request と Authorization Server の policy にも依存します。

## 4. Access Token Request での `resource`

RFC 8707 §2.2 では、Token Endpoint への Access Token Request に `resource` を指定すると、Client が requested Access Token を使用する target service または protected resource を示します。この意味は grant type にかかわらず適用されます。

Authorization Server が Access Token Request でどの `resource` value を受け入れるかは、local policy または configuration に基づく Authorization Server の裁量です。

`authorization_code` または `refresh_token` grant の場合、Authorization Server の policy は、受け入れる Resource を Resource Owner が当初 grant した Resource またはその subset に限定できます。

Authorization Code Grant で、Token Request の Resource が当初 grant された Resource の subset である場合、Authorization Server はその subset に基づく Access Token を発行します。一方、その response で Refresh Token が返される場合、その Refresh Token は元の grant 全体に bound されます。

## 5. `scope` と `resource` が示すものは同じではない

RFC 8707 §1 は、`scope` は通常「どの access が要求されているか」を表し、その access が「どこで使用されるか」を表すものではないと説明しています。

RFC 8707 §2.2 では、Client は `resource` で requested token の target service を示し、`scope` で requested token の desired scope を示せます。

したがって RFC 8707 が定義する `resource` の論点は、scope value の設計そのものではなく、requested Access Token の使用先となる Resource の identity を Authorization Server に伝えることです。

## 6. Authorization Server は Access Token を Resource に audience-restrict する

RFC 8707 §2 は、Authorization Server が `resource` parameter で示された Resource に対して、発行する Access Token を audience-restrict するべきであると規定しています（SHOULD）。

Audience restriction は JWT の `aud` claim で表現できます。また、Token Introspection response では top-level の `aud` member で表現できます。

Authorization Server は `resource` value そのものを audience として使用する場合もあれば、その値からより一般的な URI または abstract identifier に map する場合もあります。RFC 8707 は、この mapping を一意の方式に固定していません。

## 7. `invalid_target`

RFC 8707 §2 は `invalid_target` error を定義しています。requested Resource が invalid、missing、unknown、malformed のいずれかである場合に Authorization Server が使用できる error code です。

また、要求された Resource と scope の組み合わせが invalid であることを Client に伝えるためにも使用できます。

## 8. Security Considerations における Resource の指定

RFC 8707 §3 は、Resource に audience-restricted された Access Token について、その Resource に正当に提示された token を別 Resource へ持ち出して不正アクセスに使用できないという性質を説明しています。`resource` parameter は、Authorization Server が requested Resource に応じた audience restriction を Access Token に適用するための情報を提供します。

multi-tenant server について RFC 8707 §3 は、tenant を識別する URI の部分を含む具体的な Resource URI を使用することの重要性を説明しています。

また、Token Request には複数の `resource` parameter を含められますが、RFC 8707 §3 は単一の `resource` parameter の使用を encouraged としています。この記述は BCP 14 の大文字の規範語ではありません。

## 一次資料

- RFC Editor: [RFC 8707 — Resource Indicators for OAuth 2.0](https://www.rfc-editor.org/rfc/rfc8707.html)

参照した主要節: §1, §2, §2.1, §2.2, §3  
最終確認: 2026-09-19
