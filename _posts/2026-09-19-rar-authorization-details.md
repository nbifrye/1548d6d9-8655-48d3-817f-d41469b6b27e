---
layout: post
title: "RFC 9396：authorization_details は認可要求をどう表現するのか"
date: 2026-09-19 02:47:00 +0900
categories: [authorization, oauth]
---

RFC 9396 **OAuth 2.0 Rich Authorization Requests** は、OAuth の認可要求に細粒度の認可データを載せるための `authorization_details` パラメータを定義します。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** OAuth Authorization Server / Client / Resource Server の実装・レビューを担当する開発者  
**この記事で伝えること:** `authorization_details` のデータ構造と、Authorization Request から Access Token に対応する権限情報が渡るまでの仕様上の関係  
**扱わないこと:** 個別業界の authorization details type 設計、PAR の詳細フロー、JWT Access Token の一般的な検証、Resource Server の業務ロジック

## 1. `authorization_details` が表現するもの

RFC 9396 §2 は、`authorization_details` を JSON object の配列として定義しています。各 object は、ある種類の resource に対する認可要件を表します。

各 object の `type` field は REQUIRED です。`type` の値によって、その object で利用できる field と値の意味が決まります。同じ `type` の entry を配列内に複数含めることも MAY とされています。

RFC 9396 §2.2 は、API 間で再利用できる common data field として、`locations`、`actions`、`datatypes`、`identifier` などを定義しています。ただし、仕様は API にこれらの field の使用を要求していません。許容される値は、保護対象 API と `type` の定義によって決まります。

## 2. Authorization Request での位置

RFC 9396 §3 により、`authorization_details` は `scope` が認可要件の指定に使われる場所で利用できます。

Authorization Request では、Client が `authorization_details` を Authorization Server に送ります。Authorization Server は、その内容を認可処理に利用します。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    participant RS as Resource Server
    C->>AS: Authorization Request + authorization_details
    AS->>AS: type / fields を検証
    AS->>AS: 認可処理
    AS-->>C: Authorization Response
    C->>AS: Token Request
    AS-->>C: Access Token + authorization_details
    C->>RS: Access Token
    RS->>RS: 対応する認可情報を強制
</pre>

この図は、`authorization_details` の処理位置だけを示しています。Authorization Code Grant の User Agent 経由の redirect など、この記事の主題ではないメッセージは省略しています。

## 3. `scope` と同時に使う場合

RFC 9396 §3.1 は、`authorization_details` と `scope` を同じ Authorization Request で使用できると定めています。この場合、それぞれは独立した認可要件を運びます。

Authorization Server は、両方が指定された場合、その request に対して両方の要件を組み合わせて処理しなければなりません（MUST）。Resource Owner から consent を得る際も、Authorization Server は両方を統合した要件を提示しなければなりません（MUST）。

一方、両者をどのように組み合わせるかの詳細は、保護対象 API に固有であり RFC 9396 の範囲外です。

## 4. Authorization Server が拒否するデータ

RFC 9396 §5 は、Authorization Server が未知の authorization details type、または type definition に適合しない authorization details を処理してはならないことを定めています。

Authorization Server は、たとえば次の条件に該当する場合、処理を中止して `invalid_authorization_details` error を返さなければなりません（MUST）。

- 未知の `type` が指定されている。
- 既知の `type` だが未知の field を含む。
- field のデータ型が type definition と一致しない。
- field の値が type definition に対して無効である。
- type definition が要求する field が欠けている。

この検証は、`authorization_details` が任意の JSON object を自由に渡す仕組みではなく、Authorization Server が理解する type definition に基づくデータであることを示します。

## 5. Token Response との関係

RFC 9396 §7 は、Authorization Server が Token Response に、Resource Owner によって認可され、対象 Access Token に割り当てられた `authorization_details` を返さなければならないことを定めています（MUST）。

Token Request に `authorization_details` が指定されている場合、Access Token に割り当てられる authorization details はその request parameter によって決まります。Client が Token Request で指定しない場合は、Authorization Server が結果を決定します。

また、Authorization Server は `authorization_details` 内の値を Client への response から省略してもよいとされています（MAY）。

## 6. Resource Server が認可を強制できるようにする

RFC 9396 §9 は、認可プロセスで承認された authorization details を Resource Server が強制できるようにするため、Authorization Server がそのデータを Resource Server に利用可能にしなければならないと定めています（MUST）。

その方法として、Authorization Server は JWT 形式の Access Token または Token Introspection Response に `authorization_details` を含めることができます（MAY）。

JWT Access Token の場合、RFC 9396 §9.1 は audience に応じて filter した authorization details object を top-level claim として追加することを RECOMMENDED としています。

Token Introspection を使う場合、§9.2 は authorization detail information を response に含めるなら、`authorization_details` という top-level member で伝達しなければならないと規定しています（MUST）。その member は §2 と同じ構造を持ち、request を行った Resource Server 向けに filter または拡張される場合があります。

## 7. データの流れ

`authorization_details` に注目すると、仕様上の関係は次のように整理できます。

<pre class="mermaid">
flowchart TD
    A[Client が認可要件を作成] --> B[authorization_details]
    B --> C[Authorization Server が type と fields を検証]
    C --> D[Resource Owner が認可]
    D --> E[Access Token に対応する authorization details]
    E --> F[Resource Server が認可情報を利用]
</pre>

RFC 9396 は、任意の2つの authorization details を一般的に比較する標準アルゴリズムを定義していません。field の意味は API の type definition に依存するためです。この記事では、その比較方法を扱いません。

## 8. 一次資料

- RFC Editor: [RFC 9396 — OAuth 2.0 Rich Authorization Requests](https://www.rfc-editor.org/rfc/rfc9396.html)

参照した主要節: §2, §2.1, §2.2, §3, §3.1, §5, §7, §9, §9.1, §9.2  
最終確認: 2026-09-19
