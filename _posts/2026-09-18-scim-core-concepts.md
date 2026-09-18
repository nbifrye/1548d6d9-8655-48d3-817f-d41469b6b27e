---
layout: post
title: "SCIM 2.0：RFC 7643 / RFC 7644 のリソースモデルとプロトコル処理"
date: 2026-09-18 09:30:00 +0900
categories: [provisioning, scim]
---

SCIM 2.0 は、identity resource を HTTP で作成・取得・更新・削除・検索するための標準です。データモデルは **RFC 7643: System for Cross-domain Identity Management: Core Schema**、プロトコルは **RFC 7644: System for Cross-domain Identity Management: Protocol** で定義されています。

この記事では RFC 7643 と RFC 7644 に記載されたリソース構造、HTTP operation、filter、PATCH、discovery、authentication / authorization の要件を整理します。MUST / SHOULD / MAY などの規範語は RFC の強度を維持して記載します。

## 1. SCIM のリソースモデル

RFC 7643 は SCIM resource を JSON で表現し、core schema と extension schema を定義します。代表的な core resource type は `User` と `Group` です。

| Resource Type | Schema URI |
|---|---|
| User | `urn:ietf:params:scim:schemas:core:2.0:User` |
| Group | `urn:ietf:params:scim:schemas:core:2.0:Group` |

Resource は `schemas` attribute に、その resource が準拠する schema URI を持ちます。RFC 7643 §3.3 は schema extension を additive として定義しており、extension は core schema に追加されます。

## 2. Common Attributes

RFC 7643 §3.1 は、原則としてすべての SCIM resource に共通する attribute を定義します。ServiceProviderConfig と ResourceType の discovery resource は例外です。

Service Provider が resource を受理した後、`id` と `meta` およびその sub-attribute には Service Provider が値を割り当てなければなりません。

代表的な common attribute は次のとおりです。

| Attribute | 意味 |
|---|---|
| `id` | Service Provider が発行する resource identifier |
| `externalId` | Provisioning Client が発行する外部 identifier |
| `meta.resourceType` | resource type |
| `meta.created` | 作成時刻 |
| `meta.lastModified` | 最終変更時刻 |
| `meta.version` | resource version |
| `meta.location` | resource の URI |

`externalId` は Provisioning Client が定義する identifier です。RFC 7643 §3.1 は、Service Provider が `externalId` を指定してはならず、Provisioning Client が発行する値として扱うことを規定しています。

## 3. Attribute characteristic

RFC 7643 は schema attribute に対して、型だけでなく動作特性も定義します。

| characteristic | 例 | 意味 |
|---|---|---|
| `type` | string, boolean, complex | attribute のデータ型 |
| `multiValued` | true / false | 複数値を持つか |
| `required` | true / false | 必須か |
| `caseExact` | true / false | 文字列比較で case-sensitive か |
| `mutability` | readOnly / readWrite / immutable / writeOnly | 変更可能性 |
| `returned` | always / never / default / request | response に返す条件 |
| `uniqueness` | none / server / global | 一意性の範囲 |
| `canonicalValues` | schema が定義する値集合 | 標準的な値 |

たとえば User の `password` は `writeOnly` で、`returned` は `never` と定義されています。

## 4. User Resource

User resource は `urn:ietf:params:scim:schemas:core:2.0:User` で識別されます。

`userName` は必須で、Service Provider 全体の User 集合の中で一意でなければなりません。その他、`name`、`displayName`、`emails`、`phoneNumbers`、`addresses`、`active`、`groups` などの attribute が定義されています。

`active` は User の administrative status を表す Boolean attribute として定義されています。

## 5. Group Resource

Group resource は `urn:ietf:params:scim:schemas:core:2.0:Group` で識別されます。

RFC 7643 §4.2 は Group resource を、common group-based または role-based access control model を表現できる resource と説明しています。ただし、SCIM 自体は明示的な authorization model を定義しません。

Group の `members` は multi-valued complex attribute です。member には resource identifier を示す `value`、SCIM resource URI を示す `$ref`、resource type を示す `type` などの sub-attribute が定義されています。

## 6. SCIM Protocol の全体フロー

RFC 7644 は HTTP method と SCIM resource endpoint を対応付けます。典型的な resource endpoint は `/Users` と `/Groups` です。

<pre class="mermaid">
sequenceDiagram
    participant C as SCIM Client
    participant SP as SCIM Service Provider
    C->>SP: GET /ServiceProviderConfig
    SP-->>C: 対応機能(PATCH / bulk / filter 等)
    C->>SP: GET /ResourceTypes / GET /Schemas
    SP-->>C: resource type / schema
    C->>SP: POST /Users
    SP-->>C: 201 Created + User resource
    C->>SP: GET /Users?filter=...
    SP-->>C: ListResponse
    C->>SP: PATCH /Users/{id}
    SP-->>C: updated resource または 204
    C->>SP: DELETE /Users/{id}
    SP-->>C: 204 No Content
</pre>

## 7. Resource の作成 — POST

RFC 7644 §3.3 は、新規 resource の作成に HTTP POST を使用します。Client は `/Users`、`/Groups` など resource type に対応する endpoint へ request を送ります。

Service Provider は schema の mutability rule に従って request attribute を処理します。たとえば readOnly attribute を Client が送信した場合の扱いは RFC 7644 §3.3 に規定されています。

Resource の作成に成功すると、Service Provider は HTTP 201 (Created) を返し、作成された resource representation を返します。Response には `Location` header で新しい resource URI が示されます。

<pre class="mermaid">
sequenceDiagram
    participant C as SCIM Client
    participant SP as Service Provider
    C->>SP: POST /Users + User representation
    SP->>SP: schema / mutability / required / uniqueness を検証
    SP->>SP: id と meta を割り当てる
    SP-->>C: 201 Created + Location + created User
</pre>

## 8. Resource の取得と検索

既知の resource は resource endpoint と `id` を組み合わせて取得します。

`GET /Users/{id}`

Collection に対する query は `GET /Users` などで実行でき、RFC 7644 §3.4.2 は `filter`、`sortBy`、`sortOrder`、`startIndex`、`count` などの query parameter を定義します。

Filter expression には、たとえば次の形式があります。

`filter=userName eq "bjensen"`

`filter=title pr and userType eq "Employee"`

`filter=emails[type eq "work" and value co "@example.com"]`

RFC 7644 は `eq`、`ne`、`co`、`sw`、`ew`、`pr`、比較演算、logical operator などを定義しています。Service Provider が指定された filter を処理できない場合、仕様に従って filter request を拒否する必要があります。

Query response は `ListResponse` schema を使用し、`totalResults`、`startIndex`、`itemsPerPage`、`Resources` などを返します。

## 9. PUT による置換

RFC 7644 §3.5.1 は HTTP PUT を resource attribute の置換に使用します。

PUT は resource 全体の representation を送信して置換する operation です。Client が事前に resource 全体を取得し、変更後の representation で置き換える例が仕様に示されています。

Service Provider は request に含まれなかった mutable attribute の扱い、readOnly attribute、immutable attribute、required attribute などを §3.5.1 の rule に従って処理します。

## 10. PATCH による部分更新

RFC 7644 §3.5.2 では HTTP PATCH は **OPTIONAL server function** と定義されています。PATCH の対応可否は `/ServiceProviderConfig` で discovery できます。

PATCH request は次の schema URI を使用します。

`urn:ietf:params:scim:api:messages:2.0:PatchOp`

`Operations` array に複数の operation を含めることができ、`op` は `add`、`remove`、`replace` のいずれかです。

<pre class="mermaid">
flowchart TD
    A[PATCH /Users/id] --> B[PatchOp schema を解析]
    B --> C{op}
    C -->|add| D[attribute/value を追加]
    C -->|remove| E[path が示す value を削除]
    C -->|replace| F[path が示す value を置換]
    D --> G[mutability と schema rule を適用]
    E --> G
    F --> G
    G --> H[更新後 resource または 204 response]
</pre>

`path` には単純な attribute path だけでなく value filter を含めることができます。RFC 7644 には、Group member を次のような path で指定して remove する例があります。

`members[value eq "..."]`

## 11. DELETE

RFC 7644 §3.6 は resource removal に HTTP DELETE を使用します。

Service Provider は内部的に resource を永久削除しない選択をしても構いません。ただし、削除後の resource に対する operation には 404 (Not Found) を返し、今後の query result から resource を除外しなければなりません。

DELETE が成功した場合、Server は HTTP 204 (No Content) を返します。

## 12. Bulk Operations

RFC 7644 §3.7 は複数の SCIM operation を1 request で送信する Bulk operation を定義します。Bulk request は次の schema URI を使用します。

`urn:ietf:params:scim:api:messages:2.0:BulkRequest`

Bulk response は次を使用します。

`urn:ietf:params:scim:api:messages:2.0:BulkResponse`

Bulk 対応の有無、および `maxOperations`、`maxPayloadSize` は Service Provider Configuration で discovery できます。

## 13. Service Provider Configuration と discovery

RFC 7644 §4 は SCIM Service Provider の機能と schema を discovery する endpoint として、次の3つを定義します。

| Endpoint | 用途 |
|---|---|
| `/ServiceProviderConfig` | PATCH、Bulk、Filter、Sort、authentication scheme 等の対応状況 |
| `/ResourceTypes` | 利用可能な resource type と endpoint |
| `/Schemas` | schema definition |

`/ServiceProviderConfig` は HTTP GET に対して、`urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig` schema の JSON object を返します。

## 14. Authentication と Authorization

RFC 7644 §2 は、SCIM 固有の authentication / authorization scheme を定義していません。SCIM は TLS および標準 HTTP authentication / authorization scheme を利用します。

仕様は例として TLS Client Authentication、Bearer Token、PoP Token、Cookie、Basic Authentication を説明しています。OAuth 2.0 Bearer Token を例に使用していますが、RFC 7644 は Bearer Token を preferred とする意図ではないことを明記しています。

Service Provider は、authenticated Client を access control policy に map し、その Client が SCIM resource を取得・更新する authorization を持つか判定できなければなりません。具体的な authorization model と mapping process は SCIM の scope 外です。

## 15. Transport Security

RFC 7644 §7.2 は SCIM が password を含む sensitive information を転送し得ることを理由として、Client と Service Provider が transport-layer security mechanism の利用を要求しなければならないと規定しています。

RFC 7644 公開時の規定では Service Provider は TLS 1.2 をサポートし、TLS 使用時に Client は server identity check を実行しなければなりません。

## 16. 一次資料

- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)
- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)

参照した主要節: RFC 7643 §2, §3, §3.1, §3.3, §4.1, §4.2, §5 / RFC 7644 §2, §2.1, §3.2–§3.7, §4, §7.2–§7.5  
最終確認: 2026-09-18
