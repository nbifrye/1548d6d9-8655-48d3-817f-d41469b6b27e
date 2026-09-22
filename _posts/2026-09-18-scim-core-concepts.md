---
layout: post
title: "SCIM 2.0 の全体像：User リソースのライフサイクルで理解する"
date: 2026-09-18 09:30:00 +0900
categories: [provisioning, scim]
---

SCIM 2.0 の基本データモデルは RFC 7643、基本プロトコルは RFC 7644 で定義されています。RFC 7643 / RFC 7644 はいずれも 2015年9月公開の Proposed Standard です。

なお、RFC 7644 はその後 RFC 9865（2025年10月、Proposed Standard、cursor-based pagination）によって更新され、RFC 7643 / RFC 7644 は RFC 9967（2026年5月、Proposed Standard、SCIM Security Events と非同期リクエスト）によって更新されています。本記事の中心である User リソースの作成・取得・更新・削除の基本処理は RFC 7643 / RFC 7644 に基づき、これらの追加機能は扱いません。

## この記事について

**記事タイプ:** Overview  
**対象読者:** SCIM 2.0 を初めて実装・接続する Provisioning Client / Service Provider の開発者  
**この記事で伝えること:** User リソースの作成・検索・更新・削除を追いながら、SCIM 2.0 の schema と HTTP protocol がどのように対応するか  
**扱わないこと:** Group membership の詳細、Bulk operation、filter grammar の完全な解説、個別の authentication scheme

この記事は RFC 7643 / RFC 7644 の全機能を順番に要約するものではありません。**1件の User リソースが Service Provider 上で作成され、取得・更新され、削除されるまで**を軸に SCIM 2.0 の全体像を説明します。

## 1. SCIM 2.0 を構成する2つの仕様

RFC 7643 は SCIM resource の schema を定義します。RFC 7644 は、その resource を HTTP で操作する protocol を定義します。

<pre class="mermaid">
flowchart TD
    A[RFC 7643 Core Schema] --> C[User Resource]
    B[RFC 7644 Protocol] --> C
    C --> D[POST: 作成]
    C --> E[GET: 取得・検索]
    C --> F[PUT / PATCH: 更新]
    C --> G[DELETE: 削除]
</pre>

User resource の schema URI は次のとおりです。

`urn:ietf:params:scim:schemas:core:2.0:User`

## 2. User リソースの基本構造

RFC 7643 は User resource に `userName`、`name`、`displayName`、`emails`、`phoneNumbers`、`addresses`、`active` などの attribute を定義しています。

`userName` は必須で、Service Provider 全体の User 集合の中で一意でなければなりません。

SCIM resource には共通 attribute もあります。

代表的な common attribute は次のとおりです。

- **`id`:** Service Provider が発行する resource identifier。
- **`externalId`:** Provisioning Client が発行する外部 identifier。
- **`meta.resourceType`:** resource type。
- **`meta.created`:** 作成時刻。
- **`meta.lastModified`:** 最終変更時刻。
- **`meta.version`:** resource version。Service Provider が versioning をサポートする場合に使用される OPTIONAL な sub-attribute。
- **`meta.location`:** resource URI。

Service Provider が resource を受理した後、`id` と `meta` およびその sub-attribute の値は Service Provider が割り当てなければなりません（MUST、RFC 7643 §3.1）。ただし、`meta.version` のサポートは OPTIONAL です。

## 3. Attribute には扱い方を示す特性が定義される

RFC 7643 の schema は、attribute の型だけでなく、その attribute をどのように扱うかを示す特性（attribute characteristic）も定義します。

主な attribute characteristic は次のとおりです。

- **`type`:** `string`、`boolean`、`complex` などのデータ型。
- **`multiValued`:** 複数値を持てるか。
- **`required`:** 必須 attribute か。
- **`caseExact`:** 文字列比較が case-sensitive か。
- **`mutability`:** `readOnly`、`readWrite`、`immutable`、`writeOnly`。
- **`returned`:** `always`、`never`、`default`、`request`。
- **`uniqueness`:** `none`、`server`、`global`。

Service Provider は POST、PUT、PATCH を処理する際に、これらの schema rule を適用します。

## 4. User を作成する

RFC 7644 §3.3 は、新しい resource の作成に HTTP POST を使用します。

<pre class="mermaid">
sequenceDiagram
    participant C as Provisioning Client
    participant SP as Service Provider
    C->>SP: POST /Users + User representation
    SP->>SP: schema / required / mutability / uniqueness を検証
    SP->>SP: id と meta を割り当てる
    SP-->>C: 201 Created + Location + User resource
</pre>

Client は `/Users` endpoint に User representation を送信します。Service Provider は schema rule に従って request を処理し、作成に成功した場合は HTTP 201 (Created) を返さなければなりません（SHALL）。Response body には作成後の resource representation を含めることが推奨されています（SHOULD）。

Response の `Location` header には、新しい resource の URI を含めなければなりません（SHALL）。同じ URI は response body の `meta.location` にも含めなければなりません（SHALL）。

## 5. 作成した User を取得する

既知の resource identifier がある場合、Client は次の形式で User を取得できます。

`GET /Users/{id}`

Collection endpoint に対して query を実行することもできます。

`GET /Users?filter=userName eq "bjensen"`

RFC 7644 §3.4.2 は、`filter`、`sortBy`、`sortOrder`、`startIndex`、`count` などの query parameter を定義しています。

検索結果は `ListResponse` schema で返されます。`totalResults` は REQUIRED で、`Resources` は `totalResults` が 0 でない場合に REQUIRED です。`startIndex` と `itemsPerPage` は pagination により部分的な結果を返す場合に REQUIRED です。

## 6. User を更新する

SCIM 2.0 には、resource を更新する方法として PUT と PATCH があります。

### 6.1 PUT

RFC 7644 §3.5.1 は HTTP PUT を resource attribute の置換に使用します。

Client は resource representation を送信し、Service Provider は schema の mutability、required などの rule に従って処理します。

### 6.2 PATCH

RFC 7644 §3.5.2 の PATCH は OPTIONAL server function です。対応可否は `/ServiceProviderConfig` で discovery できます。

PATCH request body は `schemas` attribute に次の schema URI を含めなければなりません（MUST）。

`urn:ietf:params:scim:api:messages:2.0:PatchOp`

また、request body は1つ以上の PATCH operation を格納する `Operations` array を含めなければなりません（MUST）。各 operation object は `op` member を正確に1つ持たなければならず（MUST）、その値には `add`、`remove`、`replace` のいずれかを使用できます（MAY）。

<pre class="mermaid">
flowchart TD
    A[PATCH /Users/id] --> B[PatchOp を解析]
    B --> C{op}
    C -->|add| D[値を追加]
    C -->|remove| E[値を削除]
    C -->|replace| F[値を置換]
    D --> G[schema / mutability rule を適用]
    E --> G
    F --> G
    G --> H[更新後 resource または 204]
</pre>

## 7. User を削除する

RFC 7644 §3.6 は resource removal に HTTP DELETE を使用します。

`DELETE /Users/{id}`

削除が成功した場合、Service Provider は HTTP 204 (No Content) を返さなければなりません（SHALL）。

Service Provider が内部的に resource を永久削除しない場合でも、削除後の resource に対する operation には 404 (Not Found) を返し、以後の query result から resource を除外しなければなりません。

## 8. Service Provider の機能を discovery する

SCIM 2.0 は、Client が Service Provider の対応機能を確認するための discovery endpoint を定義しています。

Discovery endpoint は次の3つです。

- **`/ServiceProviderConfig`:** PATCH、Bulk、Filter、Sort、authentication scheme などの対応状況。
- **`/ResourceTypes`:** 利用可能な resource type と endpoint。
- **`/Schemas`:** schema definition。

User resource を操作する前に、Client はこれらの endpoint を利用して Service Provider の capability と schema を取得できます。

<pre class="mermaid">
sequenceDiagram
    participant C as SCIM Client
    participant SP as Service Provider
    C->>SP: GET /ServiceProviderConfig
    SP-->>C: supported features
    C->>SP: GET /ResourceTypes
    SP-->>C: resource types and endpoints
    C->>SP: GET /Schemas
    SP-->>C: schema definitions
</pre>

## 9. User ライフサイクルとして見た SCIM 2.0

この記事で扱った User lifecycle を HTTP operation で追うと、次の順序になります。

1. **作成 — `POST /Users`:** User resource を作成する。
2. **取得 — `GET /Users/{id}`:** User resource を取得する。
3. **検索 — `GET /Users?filter=...`:** 条件に一致する User を検索する。
4. **置換 — `PUT /Users/{id}`:** resource を置換する。
5. **部分更新 — `PATCH /Users/{id}`:** attribute を部分更新する。
6. **削除 — `DELETE /Users/{id}`:** resource を削除する。

## 10. この記事で扱っていない SCIM 2.0 の主題

RFC 7643 / RFC 7644 には、このほかにも Group resource、schema extension、Bulk operation、filter grammar、sorting、index-based pagination、ETag、authentication / authorization、security considerations などが定義されています。RFC 9865 の cursor-based pagination と RFC 9967 の SCIM Security Events / 非同期リクエストも、本記事の範囲外です。

また、2026年5月公開の Proposed Standard である RFC 9944 は SCIM に Device と EndpointApp の resource type および関連 schema extension を追加していますが、本記事の User resource のライフサイクルには変更を加えません。

## 11. 一次資料

- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)
- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)
- RFC Editor: [RFC 9865 — Cursor-Based Pagination of System of Cross-domain Identity Management (SCIM) Resources](https://www.rfc-editor.org/rfc/rfc9865.html)
- RFC Editor: [RFC 9944 — Device Schema Extensions to the System for Cross-Domain Identity Management (SCIM) Model](https://www.rfc-editor.org/rfc/rfc9944.html)
- RFC Editor: [RFC 9967 — System for Cross-Domain Identity Management (SCIM) Profile for Security Event Tokens (SETs)](https://www.rfc-editor.org/rfc/rfc9967.html)

参照した主要節: RFC 7643 §2, §3, §3.1, §4.1 / RFC 7644 §3.2–§3.6, §4 / RFC 9865 §1 / RFC 9944 §1–§3 / RFC 9967 §1  
最終確認: 2026-09-23
