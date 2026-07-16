from __future__ import annotations

import pandas as pd
import streamlit as st

# Import your newly completed and verified P5 functions
from pipeline.aggregate import returns_summary, top_customers, concentration


def slide_leaks(df_sales: pd.DataFrame, df_returns: pd.DataFrame) -> None:
    """Render Slide 3 in Streamlit."""
    st.header("Slide 3: Kthimet & Klientët Kyç (Leaks & Key Customers) 📉")

    # 1. Fetch Aggregations
    ret_summary = returns_summary(df_sales, df_returns)
    top_custs = top_customers(df_sales)
    con_stats = concentration(df_sales)

    # 2. MUST: Concentration Metric (Top 5% orders)
    pct = con_stats.get("percentage", 0.0)
    order_count = con_stats.get("top_order_count", 0)
    
    st.subheader("Koncentrimi i Porosive (Order Concentration)")
    st.metric(label="Përqindja e Xhiros (Revenue Share)", value=f"{pct:.2f}%")
    st.write(
        f"Kompania varet nga një grup i vogël porosish: "
        f"**top 5%** ({order_count} porosi) sjellin **{pct:.2f}%** të të gjithë xhiros."
    )

    # 3. Two columns: Returns side vs. Customers side
    col1, col2 = st.columns(2)

    with col1:
        # MUST: Returns per month + Return rate %
        st.subheader("Kthimet Mujore & Shkalla e Kthimit %")
        st.dataframe(ret_summary)

        # MUST: Top 5 most-returned products
        st.subheader("Top 5 Produktet më të Kthyera")
        if not df_returns.empty:
            df_ret_temp = df_returns.copy()
            if "Revenue" not in df_ret_temp.columns:
                df_ret_temp["Revenue"] = df_ret_temp["Price"] * df_ret_temp["Quantity"]
            df_ret_temp["Revenue_Abs"] = df_ret_temp["Revenue"].abs()

            top_returned_prods = (
                df_ret_temp.groupby("Description")["Revenue_Abs"].sum()
                .reset_index()
                .sort_values(by="Revenue_Abs", ascending=False)
                .head(5)
                .rename(columns={"Revenue_Abs": "Vlera e Kthyer (Returned Value)"})
            )
            st.dataframe(top_returned_prods)
        else:
            st.write("Nuk ka kthime në këtë periudhë.")

    with col2:
        # MUST: Top 10 Customers
        st.subheader("Top 10 Klientët sipas Xhiros")
        st.dataframe(top_custs)

        # BONUS: "customers to call this month" table (top returns)
        st.subheader("📞 Klientët për t'u Kontaktuar (Bonus)")
        if not df_returns.empty:
            df_ret_temp = df_returns.copy()
            if "Revenue" not in df_ret_temp.columns:
                df_ret_temp["Revenue"] = df_ret_temp["Price"] * df_ret_temp["Quantity"]
            df_ret_temp["Revenue_Abs"] = df_ret_temp["Revenue"].abs()

            # Group by "Customer ID" (matching EXPECTED_COLUMNS)
            cust_col = "Customer ID"
            if cust_col in df_ret_temp.columns:
                df_ret_temp = df_ret_temp.dropna(subset=[cust_col])
                df_ret_temp[cust_col] = df_ret_temp[cust_col].astype(float).astype(int).astype(str)
                
                call_list = (
                    df_ret_temp.groupby(cust_col)["Revenue_Abs"].sum()
                    .reset_index()
                    .sort_values(by="Revenue_Abs", ascending=False)
                    .head(5)
                    .rename(columns={"Revenue_Abs": "Vlera Total e Kthyer"})
                )
                st.dataframe(call_list)
            else:
                st.write("Mungon kolona 'Customer ID'.")
        else:
            st.write("Nuk ka kthime.")

    # 4. KRIJON 'demo_shitjet.xlsx' (Saves the file directly in your root directory)
    output_filename = "demo_shitjet.xlsx"
    with pd.ExcelWriter(output_filename, engine="openpyxl") as writer:
        ret_summary.to_excel(writer, sheet_name="Kthimet Mujore", index=False)
        top_custs.to_excel(writer, sheet_name="Top 10 Klientet", index=False)
        
        # Save concentration metrics as a small sheet
        pd.DataFrame([{
            "Përqindja e Xhiros (Top 5% Orders Share)": pct,
            "Numri i Porosive (Top Order Count)": order_count
        }]).to_excel(writer, sheet_name="Koncentrimi", index=False)

    # 5. Provide a simple download button in Streamlit for the sales manager
    st.write("---")
    with open(output_filename, "rb") as f:
        st.download_button(
            label="📥 Shkarko demo_shitjet.xlsx",
            data=f,
            file_name=output_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )