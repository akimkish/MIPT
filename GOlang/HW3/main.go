package main

import (
	"errors"
	"fmt"
)

var ErrBudgetExceeded = errors.New("budget exceeded")

type Budget struct{
	Category string `json:"category"`
	Limit float64 `json:"limit"`
}

type Transaction struct{
	ID int
	Amount float64
	Category string
}

type Ledger struct{
	transactions []Transaction
	budgets map[string]Budget
}

func NewLedger() *Ledger{
	return &Ledger{
		budgets: make(map[string]Budget),
	}
}

func (l *Ledger) SetBudget (b Budget){
	l.budgets[b.Category] = b
}
func (l *Ledger) AddTransaction(tx Transaction) error{
	if budget, ok := l.budgets[tx.Category]; ok {
		var spent float64
		for _, t := range l.transactions{
			if t.Category == tx.Category{
				spent += t.Amount
			}
		}
		if spent+tx.Amount > budget.Limit{
			return ErrBudgetExceeded
		}
	}
	l.transactions = append(l.transactions, tx)
	return nil 
}

func main() {
	ledger := NewLedger()

	ledger.SetBudget(Budget{Category: "Еда", Limit: 5000})
	ledger.SetBudget(Budget{Category: "Транспорт", Limit: 1000})

	txs := []Transaction{
		{ID: 1, Amount: 3000, Category: "Еда"},
		{ID: 2, Amount: 1500, Category: "Еда"},
		{ID: 3, Amount: 1000, Category: "Еда"}, 
		{ID: 4, Amount: 9999, Category: "Одежда"},
	}

	for _, tx := range txs{
		if err := ledger.AddTransaction(tx); err != nil {
			if errors.Is(err, ErrBudgetExceeded) {
				fmt.Printf("транзакция %d отклонена: %v\n", tx.ID, err)
				continue
			}
			fmt.Printf("транзакция %d: неожиданная ошибка: %v\n", tx.ID, err)
			continue
		}
		fmt.Printf("транзакция %d добавлена\n", tx.ID)
	}
	fmt.Println("всего транзакций:", len(ledger.transactions))
}

