import streamlit as st


def mostrar_panel_admin(supabase_instance):
    """
    Panel de control administrativo para anulación y borrado de pedidos.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Zona de Control Admin")

    # Caja para ingresar el número de pedido a eliminar
    pedido_a_borrar = st.sidebar.text_input(
        "N° de Pedido Fuxion a eliminar:", key="admin_del_input"
    )

    if st.sidebar.button("🚨 Buscar y Eliminar Pedido"):
        if pedido_a_borrar:
            try:
                # 1. Buscamos en la tabla correcta: "entradas" (NO "inventario")
                chequeo = (
                    supabase_instance.table("entradas")
                    .select("*")
                    .eq("numero_pedido", pedido_a_borrar)
                    .execute()
                )

                if chequeo.data:
                    # 2. Borramos en la tabla "entradas"
                    supabase_instance.table("entradas").delete().eq(
                        "numero_pedido", pedido_a_borrar
                    ).execute()

                    st.sidebar.success(
                        f"Pedido N° {pedido_a_borrar} eliminado con éxito."
                    )
                    # Refrescamos la página para que desaparezca visualmente
                    st.session_state.limpiador += 1
                    st.rerun()
                else:
                    st.sidebar.error(
                        "El número de pedido no existe en la base de datos."
                    )
            except Exception as e:
                st.sidebar.error(f"Error técnico: {e}")
        else:
            st.sidebar.warning("Por favor, ingrese un número de pedido válido.")
