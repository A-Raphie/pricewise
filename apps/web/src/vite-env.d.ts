/// <reference types="vite/client" />

// Injected EIP-1193 wallet providers (OKX Wallet / MetaMask / Rabby, etc.)
declare global {
  interface Window {
    ethereum?: any
    okxwallet?: any
  }
}

export {}
