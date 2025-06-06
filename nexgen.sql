-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Tempo de geração: 06/06/2025 às 20:07
-- Versão do servidor: 10.4.32-MariaDB
-- Versão do PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `nexgen`
--

DELIMITER $$
--
-- Procedimentos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `autenticar_usuario` (IN `p_email` VARCHAR(100), IN `p_senha` VARCHAR(255))   BEGIN
    DECLARE v_id INT;
    DECLARE v_nome VARCHAR(100);
    DECLARE v_senha_hash VARCHAR(255);
    
    SELECT id, nome, senha INTO v_id, v_nome, v_senha_hash 
    FROM usuarios 
    WHERE email = p_email AND ativo = TRUE;
    
    IF v_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Usuário não encontrado';
    ELSEIF NOT (v_senha_hash = p_senha) THEN -- Na prática, você usaria bcrypt no aplicativo
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Senha incorreta';
    ELSE
        SELECT v_id AS id, v_nome AS nome;
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `criar_token_recuperacao` (IN `p_email` VARCHAR(100), IN `p_token` VARCHAR(255), IN `p_expiracao` DATETIME)   BEGIN
    DECLARE v_usuario_id INT;
    
    SELECT id INTO v_usuario_id FROM usuarios WHERE email = p_email;
    
    IF v_usuario_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'E-mail não encontrado';
    ELSE
        -- Invalida tokens anteriores não utilizados
        UPDATE tokens_recuperacao SET utilizado = TRUE 
        WHERE usuario_id = v_usuario_id AND utilizado = FALSE;
        
        -- Insere novo token
        INSERT INTO tokens_recuperacao (usuario_id, token, expiracao)
        VALUES (v_useria_id, p_token, p_expiracao);
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `registrar_usuario` (IN `p_nome` VARCHAR(100), IN `p_email` VARCHAR(100), IN `p_senha` VARCHAR(255))   BEGIN
    DECLARE user_count INT;
    
    SELECT COUNT(*) INTO user_count FROM usuarios WHERE email = p_email;
    
    IF user_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'E-mail já cadastrado';
    ELSE
        INSERT INTO usuarios (nome, email, senha) VALUES (p_nome, p_email, p_senha);
    END IF;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `autenticacao_social`
--

CREATE TABLE `autenticacao_social` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `provedor` enum('google','microsoft') NOT NULL,
  `id_provedor` varchar(255) NOT NULL,
  `data_vinculo` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `logs_autenticacao`
--

CREATE TABLE `logs_autenticacao` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `acao` enum('login','logout','registro','recuperacao_senha') NOT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `data_hora` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `logs_autenticacao`
--

INSERT INTO `logs_autenticacao` (`id`, `usuario_id`, `acao`, `ip`, `user_agent`, `data_hora`) VALUES
(1, 2, 'registro', NULL, NULL, '2025-06-06 14:56:45'),
(2, 2, 'login', NULL, NULL, '2025-06-06 14:58:39');

-- --------------------------------------------------------

--
-- Estrutura para tabela `tokens_recuperacao`
--

CREATE TABLE `tokens_recuperacao` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `expiracao` datetime NOT NULL,
  `utilizado` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nome` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `senha` varchar(255) NOT NULL,
  `data_criacao` datetime DEFAULT current_timestamp(),
  `data_atualizacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `ativo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `usuarios`
--

INSERT INTO `usuarios` (`id`, `nome`, `email`, `senha`, `data_criacao`, `data_atualizacao`, `ativo`) VALUES
(1, 'Administrador', 'admin@nexgen.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', '2025-06-06 14:45:16', '2025-06-06 14:45:16', 1),
(2, 'Teste User', 'teste@example.com', '$2b$12$89QURn56I8vibzAyEFy9eeVB1KgbRI.zlrq9gZ5nwQKJj3J4rT/YW', '2025-06-06 14:56:45', '2025-06-06 14:56:45', 1);

--
-- Índices para tabelas despejadas
--

--
-- Índices de tabela `autenticacao_social`
--
ALTER TABLE `autenticacao_social`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `provedor` (`provedor`,`id_provedor`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Índices de tabela `logs_autenticacao`
--
ALTER TABLE `logs_autenticacao`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_logs_autenticacao_usuario` (`usuario_id`),
  ADD KEY `idx_logs_autenticacao_acao` (`acao`),
  ADD KEY `idx_logs_autenticacao_data` (`data_hora`);

--
-- Índices de tabela `tokens_recuperacao`
--
ALTER TABLE `tokens_recuperacao`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `idx_tokens_recuperacao_token` (`token`),
  ADD KEY `idx_tokens_recuperacao_expiracao` (`expiracao`),
  ADD KEY `idx_tokens_recuperacao_utilizado` (`utilizado`);

--
-- Índices de tabela `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_usuarios_email` (`email`),
  ADD KEY `idx_usuarios_ativo` (`ativo`);

--
-- AUTO_INCREMENT para tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `autenticacao_social`
--
ALTER TABLE `autenticacao_social`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `logs_autenticacao`
--
ALTER TABLE `logs_autenticacao`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de tabela `tokens_recuperacao`
--
ALTER TABLE `tokens_recuperacao`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Restrições para tabelas despejadas
--

--
-- Restrições para tabelas `autenticacao_social`
--
ALTER TABLE `autenticacao_social`
  ADD CONSTRAINT `autenticacao_social_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Restrições para tabelas `logs_autenticacao`
--
ALTER TABLE `logs_autenticacao`
  ADD CONSTRAINT `logs_autenticacao_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL;

--
-- Restrições para tabelas `tokens_recuperacao`
--
ALTER TABLE `tokens_recuperacao`
  ADD CONSTRAINT `tokens_recuperacao_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
