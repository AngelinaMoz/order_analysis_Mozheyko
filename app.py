import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import streamlit as st

#загрузка данных
@st.cache_data
def load_data(
    orders_path='orders.csv',
    users_path='users.csv',
    items_path='items.csv'
):
    orders = pd.read_csv(orders_path)
    users = pd.read_csv(users_path)
    items = pd.read_csv(items_path)
    return orders, users, items

orders, users, items = load_data()

st.set_page_config(
  page_title="Дашборд продаж",
  layout="wide"
)
st.title("Анализ эффективности работы интернет-магазина")

#объединение таблиц
orders_users = orders.merge(users, on='user_id', how='left')
full_data = orders_users.merge(items, on='item_id', how='left')

#поиск и удаление пропусков
full_data_before = full_data.copy()
def check_missing(df):
  missing = full_data.isnull().sum()
  missing_cols = missing[missing>0]

  if len(missing_cols) == 0:
    print("Пропусков нет")
  else:
    print("Пропуски найдены в столбцах:")
    for col, count in missing_cols.items():
      print(f" {col}: {count}")

check_missing(full_data)

rows_before = len(full_data_before)
full_data = full_data.dropna(subset=['order_id'])
rows_after = len(full_data)
print(f"Удалено строк с пропущенным order_id: {rows_before - rows_after}")

#преобразование столбцов
full_data_before = full_data.copy()
full_data['order_date'] = pd.to_datetime(full_data['order_date'], errors='coerce')
full_data['registration_date'] = pd.to_datetime(full_data['registration_date'], errors='coerce')
print(full_data['registration_date'].dtype)

dtypes_before = full_data_before.dtypes
dtypes = full_data.dtypes

comparison_dtype = pd.DataFrame({
  'До': dtypes_before,
  'После': dtypes
})
print(comparison_dtype)

st.subheader("Исходные данные")

#блок «Сырые данные»

with st.sidebar:
  st.header("Фильтры")

  selected_category = st.selectbox(
    label="Выберите категорию:",
    options=['Все'] + list(full_data['category'].unique())
  )

if selected_category == 'Все':
  filtered_full_data = full_data
else:
  filtered_full_data = full_data[full_data['category'] == selected_category]

min_date = full_data['order_date'].min().date()
max_date = full_data['order_date'].max().date()
selected_date_range = st.date_input(
  label="Выберите диапазон дат:",
  value=(min_date, max_date),
  min_value=min_date,
  max_value=max_date
  )

if len(selected_date_range) == 2:
  start_date, end_date = selected_date_range
  filtered_full_data = filtered_full_data[
    (filtered_full_data['order_date'].dt.date >= start_date) &
    (filtered_full_data['order_date'].dt.date <= end_date)
  ]
  
st.dataframe(filtered_full_data)

#блок «Ключевые показатели»

st.markdown("<h3 style='text-align: center;'>Ключевые показатели</h3>", unsafe_allow_html=True)
st.write("")
st.write("")

total_orders = filtered_full_data['order_id'].nunique()

total_revenue = round((filtered_full_data['price_per_unit'] * filtered_full_data['quantity']).sum())

users_unique = filtered_full_data['user_id'].nunique()

if total_orders > 0:
  check_avg = round(total_revenue / total_orders)
else:
  check_avg = 0

col1, col2 = st.columns(2)
with col1:
  st.metric(label="Общее количество заказов", value=total_orders)
  st.metric(label="Общая выручка", value=f"{total_revenue:,.2f} руб.")

with col2:
  st.metric(label="Количество уникальных пользователей", value=users_unique)
  st.metric(label="Средний чек", value=f"{check_avg:,.2f} руб.")

#блок «Визуализация»

st.markdown("<h3 style='text-align: center;'>Визуализация</h3>", unsafe_allow_html=True)
st.write("")
st.write("")

top_items = (filtered_full_data.groupby('item_name').apply(lambda x: (x['price_per_unit'] * x['quantity']).sum()).sort_values(ascending=False).head(10))

fig1, ax = plt.subplots(figsize=(8,6))

ax.tick_params(axis='y', labelsize=18)
ax.barh(top_items.index, top_items.values, color='#800000')
ax.set_xlabel("Выручка, руб", fontsize=26)
ax.set_title("Топ-10 товаров по выручке", fontsize=28)
ax.invert_yaxis()

filtered_full_data['day_of_week'] = filtered_full_data['order_date'].dt.day_name()
orders_by_day = filtered_full_data['day_of_week'].value_counts()

ru_map = {'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср',
  'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'
  }
orders_by_day.index = orders_by_day.index.map(ru_map)
ru_order = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
orders_by_day = orders_by_day.reindex(ru_order, fill_value=0)

fig2, ax = plt.subplots(figsize=(8,6))
ax.bar(orders_by_day.index, orders_by_day.values, color='#800000')
ax.set_xlabel("День недели", fontsize=18)
ax.set_ylabel("Количество заказов", fontsize=18)
ax.set_title('Зависимость количества заказов от дня недели', fontsize=20)

col1, col2 = st.columns(2)

with col1:
  st.pyplot(fig1, use_container_width=False)
with col2:
  st.pyplot(fig2, use_container_width=False)

revenue_by_category = (
  filtered_full_data.groupby('category')
  .apply(lambda x: (x['price_per_unit'] * x['quantity']).sum())
  .sort_values(ascending=False)
)

colors = cm.Reds(np.linspace(0.3, 0.9, len(revenue_by_category)))

fig3, ax3 = plt.subplots(figsize=(5, 5))

wedges, texts, autotexts = ax3.pie(
  revenue_by_category.values,
  autopct='%1.1f%%',
  startangle=90,
  colors=colors,
  pctdistance=0.9,
  textprops={'fontsize': 6}
)

ax3.legend(
  wedges,
  revenue_by_category.index,
  title="Категории",
  loc="center left",
  bbox_to_anchor=(1, 0, 0.5, 1),
  fontsize=9
)

ax3.set_title("Доля категорий в общей выручке", fontsize=10)
st.pyplot(fig3, use_container_width=False)

#блок "Аналитические выводы"

st.markdown("<h3 style='text-align: center;'>Аналитические выводы</h3>", unsafe_allow_html=True)
st.write("")
st.write("")

top_category = revenue_by_category.index[0]
top_category_revenue = round(revenue_by_category.iloc[0])

best_day = orders_by_day.idxmax()
best_day_count = orders_by_day.max()

top_item_name = top_items.index[0]
top_item_revenue = round(top_items.iloc[0])

st.write(f"Основная выручка приходится на категорию {top_category}: {top_category_revenue} руб.")
st.write(f"Пик заказов наблюдается в {best_day}: {best_day_count} заказов")
st.write(f"Товар {top_item_name} является лидером продаж, выруска по нему составила {top_item_revenue} руб.")