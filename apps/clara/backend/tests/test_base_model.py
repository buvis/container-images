from clara.base.model import VaultScopedModel


def test_vault_scoped_model_is_abstract():
    assert VaultScopedModel.__abstract__ is True
