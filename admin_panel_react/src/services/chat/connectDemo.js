export async function connectDemo() {
    // Simula una conexi�n "ok"
    await new Promise((r) => setTimeout(r, 600));
    return true;
}