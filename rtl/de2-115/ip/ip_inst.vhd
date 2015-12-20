	component ip is
		port (
			clk        : in  std_logic                     := 'X';             -- clk
			reset      : in  std_logic                     := 'X';             -- reset
			address    : in  std_logic                     := 'X';             -- address
			chipselect : in  std_logic                     := 'X';             -- chipselect
			byteenable : in  std_logic_vector(3 downto 0)  := (others => 'X'); -- byteenable
			read       : in  std_logic                     := 'X';             -- read
			write      : in  std_logic                     := 'X';             -- write
			writedata  : in  std_logic_vector(31 downto 0) := (others => 'X'); -- writedata
			readdata   : out std_logic_vector(31 downto 0);                    -- readdata
			irq        : out std_logic;                                        -- irq
			UART_RXD   : in  std_logic                     := 'X';             -- RXD
			UART_TXD   : out std_logic                                         -- TXD
		);
	end component ip;

	u0 : component ip
		port map (
			clk        => CONNECTED_TO_clk,        --                clk.clk
			reset      => CONNECTED_TO_reset,      --              reset.reset
			address    => CONNECTED_TO_address,    -- avalon_rs232_slave.address
			chipselect => CONNECTED_TO_chipselect, --                   .chipselect
			byteenable => CONNECTED_TO_byteenable, --                   .byteenable
			read       => CONNECTED_TO_read,       --                   .read
			write      => CONNECTED_TO_write,      --                   .write
			writedata  => CONNECTED_TO_writedata,  --                   .writedata
			readdata   => CONNECTED_TO_readdata,   --                   .readdata
			irq        => CONNECTED_TO_irq,        --          interrupt.irq
			UART_RXD   => CONNECTED_TO_UART_RXD,   -- external_interface.RXD
			UART_TXD   => CONNECTED_TO_UART_TXD    --                   .TXD
		);

