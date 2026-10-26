/*
 * NikoAssist Local — offline Android chat.
 * GPL-3.0-or-later (Niko Studio Design).
 * Uses the MIT-licensed llama.cpp Android example inference library.
 *
 * No network permissions, cloud account, backend, keys or remote inference.
 */
package com.example.llama

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.arm.aichat.AiChat
import com.arm.aichat.InferenceEngine
import com.google.android.material.floatingactionbutton.FloatingActionButton
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.DataInputStream
import java.io.File
import java.io.FileOutputStream
import java.util.UUID

/**
 * First working local-only chat for Snapdragon 865 / arm64.
 * All GGUF bytes and the generated conversation remain on the phone.
 * Model is user-selected, copied once into app-private storage, then
 * automatically loaded after restarts. Replies are produced via llama.cpp.
 *
 * This screen intentionally does not expose unrestricted device-agent tools.
 */
class MainActivity : AppCompatActivity() {
    private lateinit var info: TextView
    private lateinit var history: RecyclerView
    private lateinit var input: EditText
    private lateinit var action: FloatingActionButton

    private var engine: InferenceEngine? = null
    private var generation: Job? = null
    private var ready = false
    private val messages = mutableListOf<Message>()
    private val adapter = MessageAdapter(messages)

    private val chooseModel = registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) importModel(uri)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)

        info = findViewById(R.id.gguf)
        history = findViewById(R.id.messages)
        input = findViewById(R.id.user_input)
        action = findViewById(R.id.fab)
        history.layoutManager = LinearLayoutManager(this).apply { stackFromEnd = true }
        history.adapter = adapter

        info.text = INSTRUCTIONS
        info.setOnClickListener {
            if (!ready) {
                runCatching {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(MODEL_URL)))
                }.onFailure { showError("Ouvre le lien du modèle dans ton navigateur.") }
            }
        }

        action.isEnabled = false
        action.setOnClickListener {
            if (ready) send() else chooseModel.launch(arrayOf("*/*"))
        }

        lifecycleScope.launch(Dispatchers.Default) {
            try {
                val local = AiChat.getInferenceEngine(applicationContext)
                engine = local
                val file = modelFile()
                if (file.isFile && file.length() > MIN_MODEL_BYTES) {
                    status("Chargement du modèle local…")
                    local.loadModel(file.absolutePath)
                    withContext(Dispatchers.Main) { modelReady() }
                } else {
                    withContext(Dispatchers.Main) {
                        action.isEnabled = true
                        action.setImageResource(R.drawable.outline_folder_open_24)
                    }
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                showError("Initialisation locale impossible : ${e.message ?: "erreur inconnue"}")
                withContext(Dispatchers.Main) { action.isEnabled = true }
            }
        }
    }

    private fun importModel(uri: Uri) {
        if (generation?.isActive == true || ready) return
        action.isEnabled = false
        input.isEnabled = false
        lifecycleScope.launch(Dispatchers.IO) {
            val part = File(filesDir, "models/model.gguf.part")
            try {
                status("Copie du modèle GGUF dans le stockage privé…")
                part.parentFile?.mkdirs()
                contentResolver.openInputStream(uri)?.use { source ->
                    DataInputStream(source).use { stream ->
                        val magic = ByteArray(4)
                        stream.readFully(magic)
                        require(String(magic, Charsets.US_ASCII) == "GGUF") {
                            "Le fichier choisi n'est pas un modèle GGUF"
                        }
                        FileOutputStream(part).use { output ->
                            output.write(magic)
                            stream.copyTo(output, 1024 * 1024)
                            output.fd.sync()
                        }
                    }
                } ?: error("Impossible de lire le fichier sélectionné")
                require(part.length() > MIN_MODEL_BYTES) { "Fichier modèle incomplet" }
                val final = modelFile()
                check(part.renameTo(final)) { "Impossible d'enregistrer le modèle" }
                status("Chargement du modèle sur le téléphone…")
                val local = engine ?: error("Moteur local non initialisé")
                local.loadModel(final.absolutePath)
                withContext(Dispatchers.Main) { modelReady() }
            } catch (e: CancellationException) {
                part.delete()
                throw e
            } catch (e: Exception) {
                part.delete()
                showError("Importation impossible : ${e.message ?: "erreur inconnue"}")
                withContext(Dispatchers.Main) { action.isEnabled = true }
            }
        }
    }

    private fun modelReady() {
        ready = true
        info.text = "NikoAssist Local · IA hors ligne activée\nModèle sur le téléphone. Aucune connexion ni clé API nécessaire."
        input.isEnabled = true
        input.hint = "Écris ton message en français…"
        action.setImageResource(R.drawable.outline_send_24)
        action.isEnabled = true
    }

    private fun send() {
        val prompt = input.text?.toString()?.trim().orEmpty()
        if (prompt.isEmpty() || generation?.isActive == true) return
        val local = engine ?: return
        input.text?.clear()
        input.isEnabled = false
        action.isEnabled = false
        messages.add(Message(UUID.randomUUID().toString(), prompt, true))
        adapter.notifyItemInserted(messages.lastIndex)
        val index = messages.size
        messages.add(Message(UUID.randomUUID().toString(), "", false))
        adapter.notifyItemInserted(index)
        history.scrollToPosition(index)

        val text = StringBuilder()
        generation = lifecycleScope.launch(Dispatchers.Default) {
            try {
                local.sendUserPrompt(prompt).onCompletion { cause ->
                    if (cause != null && cause !is CancellationException) {
                        showError("Génération interrompue : ${cause.message}")
                    }
                }.collect { token ->
                    withContext(Dispatchers.Main) {
                        text.append(token)
                        messages[index] = messages[index].copy(content = text.toString())
                        adapter.notifyItemChanged(index)
                        history.scrollToPosition(index)
                    }
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                showError("Réponse locale impossible : ${e.message ?: "erreur inconnue"}")
            } finally {
                withContext(NonCancellable + Dispatchers.Main) {
                    input.isEnabled = true
                    action.isEnabled = true
                }
            }
        }
    }

    private fun modelFile(): File = File(filesDir, "models/model.gguf")

    private suspend fun status(text: String) {
        withContext(Dispatchers.Main) { info.text = text }
    }

    private fun showError(text: String) {
        runOnUiThread {
            info.text = text + "\n\n" + INSTRUCTIONS
            Toast.makeText(this, text, Toast.LENGTH_LONG).show()
        }
    }

    override fun onStop() {
        generation?.cancel()
        super.onStop()
    }

    override fun onDestroy() {
        generation?.cancel()
        engine?.destroy()
        engine = null
        super.onDestroy()
    }

    companion object {
        private const val MIN_MODEL_BYTES = 100_000_000L
        private const val MODEL_URL =
            "https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"
        private const val INSTRUCTIONS =
            "NikoAssist Local — 100 % gratuit, sans serveur.\n\n" +
            "1. Touche ce texte pour télécharger Qwen3 0.6B (~397 Mo) dans ton navigateur.\n" +
            "2. Reviens ici et touche le bouton dossier pour choisir le fichier .gguf.\n" +
            "3. Patiente pendant l'import et le chargement ; discute ensuite hors ligne.\n\n" +
            "Les réponses et les calculs restent sur ton téléphone."
    }
}
