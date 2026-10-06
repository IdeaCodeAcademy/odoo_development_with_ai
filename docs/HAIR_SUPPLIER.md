# Seller Management

`hair_supplier` extends standard Contacts with seller status, company, configurable
seller type, alternative phone, township and notes. Archive sellers to retain history.
Buyers create/edit sellers. Managers and Administrators can read/write optional NRC;
field-level protection applies to views, ORM, RPC, search and imports. Existing
contact permissions do not grant seller management. Company isolation applies to
all sellers. Purchase statistics will be added by hair_purchase.

Seven automated tests cover seller mutations, NRC protection, imports, unrelated
contact permissions, company isolation, validation and form visibility.
