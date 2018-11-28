from django.db import models

class Transaction(models.Model):
	"""
	This is a table for Faucet transaction tracking. 
	Example: bicon.tracker.solidwallet.io
	"""
	TxHash = models.CharField(max_length=70)
	Block = models.IntegerField()
	Age = models.DateField(auto_now_add=True)
	From_Wallet = models.CharField(max_length=50)
	To_Wallet = models.CharField(max_length=50)
	Amount = models.DecimalField(max_digits=20, decimal_places=12) 
	TxFee = models.DecimalField(max_digits=20, decimal_places=12)