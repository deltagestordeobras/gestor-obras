def nota_fechada(status_nota):
    return status_nota == "Fechada"


def pode_excluir_nota(df_insumos, nota_id):
    return df_insumos[df_insumos["NotaID"] == nota_id].empty


def calcular_diferenca(valor_nota, total_materiais):
    return valor_nota - total_materiais