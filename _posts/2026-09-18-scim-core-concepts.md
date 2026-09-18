---
layout: post
title: "SCIM 2.0 入門：認証ではなく『ID ライフサイクル』を標準化する"
date: 2026-09-18 09:30:00 +0900
categories: [provisioning, scim]
---

SCIM (System for Cross-domain Identity Management) はログインプロトコルではありません。組織・IdP・SaaS 等の境界をまたいで **User / Group などの identity resource を作成・更新・削除・検索するための共通モデル** を提供します。

中心は Core Schema の RFC 7643 と、HTTP ベースの Protocol の RFC 7644 です。

## OIDC / SAML との違い
OIDC や SAML は、ユーザーがサービスへアクセスするときの認証・フェデレーションで使われます。SCIM は、入社時の作成、異動時の Group 更新、退職時の無効化などアカウントライフサイクルを扱います。

## 実装で詰める点
- `externalId` とサービス側 `id` の対応
- PATCH と属性 mutability
- Group membership の大規模更新
- filter のサポート範囲
- retry 時の重複作成防止
- 退職時に削除するか `active=false` にするか
- SCIM endpoint 自体の API authorization

SCIM は強固な認証・認可方式を一つに固定する仕様ではないため、endpoint 保護は別途設計が必要です。

## 参照
- https://www.rfc-editor.org/rfc/rfc7643.html
- https://www.rfc-editor.org/rfc/rfc7644.html

最終確認: 2026-09-18
