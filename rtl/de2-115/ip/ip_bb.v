
module ip (
	clk,
	reset,
	address,
	chipselect,
	byteenable,
	read,
	write,
	writedata,
	readdata,
	irq,
	UART_RXD,
	UART_TXD);	

	input		clk;
	input		reset;
	input		address;
	input		chipselect;
	input	[3:0]	byteenable;
	input		read;
	input		write;
	input	[31:0]	writedata;
	output	[31:0]	readdata;
	output		irq;
	input		UART_RXD;
	output		UART_TXD;
endmodule
