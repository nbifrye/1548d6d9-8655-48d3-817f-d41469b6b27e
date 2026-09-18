---
layout: post
title: "SCIM 2.0 の全体像：User リソースのライフサイクルで理解する"
date: 2026-09-18 09:30:00 +0900
categories: [provisioning, scim]
---

SCIM 2.0 のデータモデルは RFC 7643、プロトコルは RFC 7644 で定義されています。

## この記事について

**記事タイプ:** Overview  
**対象読者:** SCIM 2.0 を初めて実装・接続する Provisioning Client / Service Provider の開発者  
**この記事で伝えること:** User リソースの作成・検索・更新・削除を追いながら、SCIM 2.0 の schema と HTTP protocol がどのように対応するか  
**扱わないこと:** Group membership の詳細、Bulk operation、filter grammar の完全な解説、個別の authentication scheme

この記事は RFC 7643 / RFC 7644 の全機能を順番に要約するものではありません。**1件の User リソースが Service Provider 上で作成され、取得・更新され、削除されるまで**を軸に SCIM 2.0 の全体像を説明します。

## 1. SCIM 2.0 を構成する2つの仕様

RFC 7643 は SCIM resource の schema を定義します。RFC 7644 は、その resource を HTTP で操作する protocol を定義します。

<pre class="mermaid">
flowchart LR
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

| Attribute | 役割 |
|---|---|
| `id` | Service Provider が発行する resource identifier |
| `externalId` | Provisioning Client が発行する外部 identifier |
| `meta.resourceType` | resource type |
| `meta.created` | 作成時刻 |
| `meta.lastModified` | 最終変更時刻 |
| `meta.version` | resource version |
| `meta.location` | resource URI |

Service Provider が resource を受理した後、`id` と `meta` およびその sub-attribute には Service Provider が値を割り当てます。

## 3. Attribute には動作特性が定義される

RFC 7643 の schema は、attribute の型だけでなく、その attribute をどのように扱うかも定義します。

| characteristic | 例 | 意味 |
|---|---|---|
| `type` | string, boolean, complex | データ型 |
| `multiValued` | true / false | 複数値を持てるか |
| `required` | true / false | 必須か |
| `caseExact` | true / false | 文字列比較が case-sensitive か |
| `mutability` | readOnly / readWrite / immutable / writeOnly | 変更可能性 |
| `returned` | always / never / default / request | response に返す条件 |
| `uniqueness` | none / server / global | 一意性の範囲 |

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

Client は `/Users` endpoint に User representation を送信します。Service Provider は schema rule に従って request を処理し、作成に成功した場合は HTTP 201 (Created) と作成後の resource representation を返します。

Response の `Location` header には、新しい resource の URI が示されます。

## 5. 作成した User を取得する

既知の resource identifier がある場合、Client は次の形式で User を取得できます。

`GET /Users/{id}`

Collection endpoint に対して query を実行することもできます。

`GET /Users?filter=userName eq "bjensen"`

RFC 7644 §3.4.2 は、`filter`、`sortBy`、`sortOrder`、`startIndex`、`count` などの query parameter を定義しています。

検索結果は `ListResponse` schema で返され、`totalResults`、`startIndex`、`itemsPerPage`、`Resources` などを含みます。

## 6. User を更新する

SCIM 2.0 には、resource を更新する方法として PUT と PATCH があります。

### 6.1 PUT

RFC 7644 §3.5.1 は HTTP PUT を resource attribute の置換に使用します。

Client は resource representation を送信し、Service Provider は schema の mutability、required などの rule に従って処理します。

### 6.2 PATCH

RFC 7644 §3.5.2 の PATCH は OPTIONAL server function です。対応可否は `/ServiceProviderConfig` で discovery できます。

PATCH request は次の schema URI を使用します。

`urn:ietf:params:scim:api:messages:2.0:PatchOp`

`Operations` array の `op` は `add`、`remove`、`replace` のいずれかです。

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

削除が成功した場合、Service Provider は HTTP 204 (No Content) を返します。

Service Provider が内部的に resource を永久削除しない場合でも、削除後の resource に対する operation には 404 (Not Found) を返し、以後の query result から resource を除外しなければなりません。

## 8. Service Provider の機能を discovery する

SCIM 2.0 は、Client が Service Provider の対応機能を確認するための discovery endpoint を定義しています。

| Endpoint | 確認できる内容 |
|---|---|
| `/ServiceProviderConfig` | PATCH、Bulk、Filter、Sort、authentication scheme など |
| `/ResourceTypes` | 利用可能な resource type と endpoint |
| `/Schemas` | schema definition |

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

この記事で扱った処理をまとめると、SCIM 2.0 の基本的な User lifecycle は次のようになります。

| 状態 | HTTP operation | 仕様上の役割 |
|---|---|---|
| 未作成 | POST /Users | User resource を作成 |
| 作成済み | GET /Users/{id} | User resource を取得 |
| 検索 | GET /Users?filter=... | 条件に一致する User を検索 |
| 更新 | PUT /Users/{id} | resource を置換 |
| 部分更新 | PATCH /Users/{id} | attribute を部分更新 |
| 削除 | DELETE /Users/{id} | resource を削除 |

## 10. この記事で扱っていない SCIM 2.0 の主題

RFC 7643 / RFC 7644 には、このほかにも Group resource、schema extension、Bulk operation、filter grammar、sorting、pagination、ETag、authentication / authorization、security considerations などが定義されています。

これらは User resource の基本ライフサイクルを使って SCIM の全体像を把握するという本記事の範囲外です。

## 11. 一次資料

- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)
- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)

参照した主要節: RFC 7643 §2, §3, §3.1, §4.1 / RFC 7644 §3.2–§3.6, §4  
最終確認: 2026-09-18
