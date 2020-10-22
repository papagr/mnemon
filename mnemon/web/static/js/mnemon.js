function update_counts() {
	$.get("/counts", function(data) {
		$(".nav-tabs span.unread-count").text(data.unread);
		$(".nav-tabs span.favorites-count").text(data.favorites);
		$(".nav-tabs span.archived-count").text(data.archived);
		$(".nav-tabs span.deleted-count").text(data.deleted);
	});
};

function back_to_list() {
	if (document.referrer.indexOf(window.location.hostname) != -1) {
		window.location.href = document.referrer;
	} else {
		window.location.href = "/";
	}
};

$("#bookmarklet").click(function(event) {
	event.preventDefault();
});

$('#back-to-list').click(function(event) {
	event.preventDefault();
	back_to_list();
});

$("#bookmarklet").editable({
	ajaxOptions : {
		type : "post",
		dataType : "text"
	},
	type : "url",
	placement : "right",
	send : "always",
	placeholder : "http://...",
	display : false,
	value : "",
	title : "Add an article to your reading list",
	success : function(response, value) {
		setTimeout(function() {
			//$("#bookmarklet").editable("option", "value", "");
			location.reload(true);
		 }, 0);
		// TODO: show message alert on success
		// TODO: update the UI accordingly without a page reload e.g.:
		//       * increase unread counter
		//       * show new entry in unread list if visible
	},
	params : function(params) {
		var data = {};
		data["url"] = params.value;
		data["token"] = params.name;
		return data;
	}
});

$(".tag-article").click(function(event) {
	event.stopPropagation();
	event.preventDefault();
	$("#" + $(this).data("editable")).editable("toggle");
});

$(".article-tags").editable({
	ajaxOptions : {
		type : "post",
		dataType : "text"
	},
	type : "text",
	placement : 'bottom',
	send : "always",
	toggle : "manual",
	display : function(tags) {
		var tagList = $(this);
		tagList.empty();
		if (tags) {
			$.each(tags.split(","), function(index, value) {
				value = $.trim(value);
				var link = $("<a>", {
					href : "/tags/" + value.replace(/ /g, '+')
				});
				var tag = $("<span>", {
					"class" : "label label-info",
					text : value
				});
				link.append(tag);
				tagList.append(link);
				tagList.append(" ");
			});
		} else {
			var tag = $("<span>", {
				"class" : "label label-default",
				text : "no tags"
			});
			tagList.append(tag);
		}
		;
	},
	title : "Add tags separated by commas.",
	params : function(params) {
		var data = {};
		data["article_id"] = params.pk;
		data["tags"] = params.value;
		return data;
	}
});

function findCurrentArticle(element) {
	return element.closest(".article");
};

function getArticleId(article) {
	return article.attr("id").replace("article-", "");
};

function fadeInHiddenButton(button) {
	button.fadeOut().removeClass('hidden').button('reset').fadeIn();
};

$(".article a.archive-article").click(function(event) {
	var currentArticle = findCurrentArticle($(this));
	var articleId = getArticleId(currentArticle);
	$.post("/archived", {
		article_id : articleId
	}, function(data) {
		currentArticle.fadeOut();
		update_counts();
	});
});

$(".article a.archive-favorite-article").click(function(event) {
	var archiveButton = $(this);
	archiveButton.button("loading");
	var currentArticle = findCurrentArticle(archiveButton);
	var articleId = getArticleId(currentArticle);
	$.post("/archived", {
		article_id : articleId
	}, function(data) {
		archiveButton.fadeOut();
		update_counts();
	});
});

$(".article a.archive-article-read").click(function(event) {
	var archiveButton = $(this);
	archiveButton.button("loading");
	var currentArticle = findCurrentArticle(archiveButton);
	var articleId = getArticleId(currentArticle);
	$.post("/archived", {
		article_id : articleId
	}, function(data) {
		archiveButton.fadeOut(function () {
			fadeInHiddenButton($(".article a.restore-article-read"));
		});
	});
});


$(".article a.restore-article").click(function(event) {
	var restoreButton = $(this);
	restoreButton.button("loading");
	var currentArticle = findCurrentArticle(restoreButton);
	var articleId = getArticleId(currentArticle);
	$.post("/unread", {
		article_id : articleId
	}, function(data) {
		currentArticle.fadeOut();
		update_counts();
	});
});

$(".article a.restore-article-read").click(function(event) {
	var restoreButton = $(this);
	restoreButton.button("loading");
	var currentArticle = findCurrentArticle(restoreButton);
	var articleId = getArticleId(currentArticle);
	$.post("/unread", {
		article_id : articleId
	}, function(data) {
		$(".article a.favorite-article span.glyphicon-star-empty").fadeIn();
		$(".article a.favorite-article span.glyphicon-star").fadeIn();
		$(".article a.purge-article-read").fadeOut();
		restoreButton.fadeOut(function () {
			fadeInHiddenButton($(".article a.archive-article-read"));
			if( !$(".article a.delete-article-read").is(':visible')) {
				fadeInHiddenButton($(".article a.delete-article-read"));
			}
			if( !$(".article a.tag-article").is(':visible')) {
				fadeInHiddenButton($(".article a.tag-article"));
			}
		});
	});
});

$(".article a.delete-article").click(function(event) {
	var deleteButton = $(this);
	deleteButton.button("loading");
	var currentArticle = findCurrentArticle(deleteButton);
	var articleId = getArticleId(currentArticle);
	$.post("/deleted", {
		article_id : articleId
	}, function(data) {
		currentArticle.fadeOut();
		update_counts();
	});
});

$(".article a.delete-article-read").click(function(event) {
	var deleteButton = $(this);
	deleteButton.button("loading");
	var currentArticle = findCurrentArticle(deleteButton);
	var articleId = getArticleId(currentArticle);
	$.post("/deleted", {
		article_id : articleId
	}, function(data) {
		deleteButton.fadeOut(function () {
			fadeInHiddenButton($(".article a.purge-article-read"));
		});
		$(".article a.tag-article").fadeOut();
		$(".article a.favorite-article span.glyphicon-star-empty").fadeOut();
		$(".article a.favorite-article span.glyphicon-star").fadeOut();
		$(".article a.archive-article-read").fadeOut(function () {
			fadeInHiddenButton($(".article a.restore-article-read"));
		});
	});
});

$(".article a.favorite-article span.glyphicon-star-empty")
	.bind("click", addToFavorites);
$(".article a.favorite-article span.glyphicon-star")
	.bind("click", removeFromFavorites);

function addToFavorites(event) {
	event.preventDefault();
	var starButton = $(this);
	var currentArticle = findCurrentArticle(starButton);
	var articleId = getArticleId(currentArticle);
	$.post("/favorites", {
		article_id : articleId
	}, function(data) {
		starButton.removeClass("glyphicon-star-empty grey")
		          .addClass("glyphicon-star gold")
                  .attr("title", "Remove from favorites")
                  .unbind("click")
			      .bind("click", removeFromFavorites);
		update_counts();
	});
};

function removeFromFavorites(event) {
	event.preventDefault();
	var starButton = $(this);
	var currentArticle = findCurrentArticle(starButton);
	var articleId = getArticleId(currentArticle);
	$.ajax({
		url : "/favorites/" + articleId,
		type : "DELETE",
		success : function(data) {
			starButton.removeClass("glyphicon-star gold")
			          .addClass("glyphicon-star-empty grey")
			          .attr("title", "Add to favorites")
			          .unbind("click")
			          .bind("click", addToFavorites);
			update_counts();
			var activeTab = $('.nav-tabs li.active');
			if (activeTab && activeTab.attr("id") === "favorites-tab") {
				currentArticle.fadeOut();
			}
		}
	});
};

$(".article a.purge-article").click(function(event) {
	var purgeButton = $(this);
	purgeButton.button("loading");
	var currentArticle = findCurrentArticle(purgeButton);
	var articleId = getArticleId(currentArticle);
	$.ajax({
		url : "/article/" + articleId,
		type : "DELETE",
		success : function(result) {
			currentArticle.fadeOut();
			update_counts();
		}
	});
});

$(".article a.purge-article-read").click(function(event) {
	var purgeButton = $(this);
	purgeButton.button("loading");
	var currentArticle = findCurrentArticle(purgeButton);
	var articleId = getArticleId(currentArticle);
	$.ajax({
		url : "/article/" + articleId,
		type : "DELETE",
		success : function(result) {
			currentArticle.fadeOut();
			update_counts();
			back_to_list();
		}
	});
});

$("#purge-all").click(function(event) {
	var purgeAllButton = $(this);
	purgeAllButton.button("loading");
	$.ajax({
		url : "/deleted",
		type : "DELETE",
		success : function(result) {
			$(".article").fadeOut();
			purgeAllButton.button("reset");
			update_counts();
		}
	});
});